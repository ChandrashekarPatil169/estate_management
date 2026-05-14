from odoo import models, fields,api,_
from markupsafe import Markup
from odoo.exceptions import ValidationError


class SoftwareAsset(models.Model):
    _name = 'software.asset'
    _description = 'Software Asset'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _order = "id desc"

    name = fields.Char(string="Software Name", required=True, track_visibility='onchange')
    vendor = fields.Char(string="Vendor", track_visibility='onchange')
    license_key = fields.Char(string="License Key", track_visibility='onchange')
    version = fields.Char(string="Version", track_visibility='onchange')
    license_type = fields.Selection([
        ('perpetual', 'Perpetual'),
        ('subscription', 'Subscription'),
        ('open_source', 'Open Source'),
    ], string="License Type",  track_visibility='onchange')
    purchase_date = fields.Date(string="Purchase Date", track_visibility='onchange')
    expiry_date = fields.Date(string="Expiry Date", track_visibility='onchange')
    assigned_to = fields.Many2one('hr.employee', string="Assigned To", track_visibility='onchange')

    renewal_ids = fields.One2many('software.renewal', 'software_id', string="Renewal History")
    installation_ids = fields.One2many('software.installation', 'software_id', string="Installation Details")
    renewal_count = fields.Integer(
        string="Renewals",
        compute="_compute_renewal_count"
    )
    license_type_id = fields.Many2one(
        'software.license.type',
        string="License Type",
        tracking=True
    )
    # warehouse_id = fields.Many2one(
    #     'inventory.warehouse',
    #     string="Warehouse",
    #     tracking=True,
    #     domain=lambda self: [
    #         ('id', 'in',
    #          self.env.user.warehouse_exec_ids.ids +
    #          self.env.user.warehouse_manager_ids.ids
    #          )
    #     ]
    # )
    allowed_warehouse_ids = fields.Many2many(
        'inventory.warehouse',
        compute='_compute_allowed_warehouses'
    )

    # 2. Update your actual warehouse field to use the helper
    warehouse_id = fields.Many2one(
        'inventory.warehouse',
        string='Warehouse',
        domain="[('id', 'in', allowed_warehouse_ids)]"
    )

    @api.depends_context('uid')
    def _compute_allowed_warehouses(self):
        for rec in self:
            user = self.env.user
            # Combine the IDs from both roles
            allowed_ids = user.warehouse_exec_ids.ids + user.warehouse_manager_ids.ids
            rec.allowed_warehouse_ids = [(6, 0, allowed_ids)]

    @api.constrains('warehouse_id')
    def _check_warehouse_access(self):
        for rec in self:
            user = rec.env.user

            is_exec = user.has_group('custom_inventory.group_warehouse_executive')
            is_manager = user.has_group('custom_inventory.group_warehouse_manager')

            exec_ids = user.warehouse_exec_ids.ids
            manager_ids = user.warehouse_manager_ids.ids

            # Decide allowed warehouses
            if is_exec and not is_manager:
                allowed_ids = exec_ids

            elif is_manager and not is_exec:
                allowed_ids = manager_ids

            elif is_exec and is_manager:
                allowed_ids = exec_ids + manager_ids

            else:
                allowed_ids = []

            # 🚨 VALIDATION
            if rec.warehouse_id and rec.warehouse_id.id not in allowed_ids:
                raise ValidationError(
                    "You are not allowed to select this warehouse based on your role."
                )

    def _validate_followers_against_warehouse(self, partners, vals=None):
        for record in self:

            warehouse = record.warehouse_id

            if vals and vals.get('warehouse_id'):
                warehouse = self.env['inventory.warehouse'].browse(vals['warehouse_id'])

            if not warehouse:
                continue

            for partner in partners:
                user = partner.user_ids[:1]

                if not user:
                    continue

                allowed_warehouses = (
                        user.warehouse_exec_ids.ids +
                        user.warehouse_manager_ids.ids
                )

                if warehouse.id not in allowed_warehouses:
                    raise ValidationError(
                        f"{user.name} is not assigned to warehouse '{warehouse.name}'."
                    )


    def _compute_renewal_count(self):
        for rec in self:
            rec.renewal_count = len(rec.renewal_ids)

    def action_view_renewals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewal History',
            'res_model': 'software.renewal',
            'view_mode': 'list,form',
            'domain': [('software_id', '=', self.id)],
            'context': {
                'default_software_id': self.id
            }
        }

    def _send_mail_to_followers(self, subject, body):
        Mail = self.env['mail.mail']

        for rec in self:
            emails = []

            for partner in rec.message_partner_ids:
                if partner.email:
                    emails.append(partner.email)

            if not emails:
                continue

            mail = Mail.create({
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(emails),
                'auto_delete': False,
            })
            mail.send()

            rec.message_post(
                subject=subject,
                body=Markup(body),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        if partner_ids:
            partners = self.env['res.partner'].browse(partner_ids)
            self._validate_followers_against_warehouse(partners)

        return super().message_subscribe(
            partner_ids=partner_ids,
            subtype_ids=subtype_ids
        )

    def write(self, vals):

        tracked_fields = ['license_key', 'license_type_id']

        email_changes_map = {}
        if 'message_partner_ids' in vals:
            partner_ids = []

            for command in vals.get('message_partner_ids'):
                if command[0] == 4:
                    partner_ids.append(command[1])
                elif command[0] == 6:
                    partner_ids.extend(command[2])

            partners = self.env['res.partner'].browse(partner_ids)
            self._validate_followers_against_warehouse(partners, vals)

        for rec in self:
            changes = []

            for field in tracked_fields:

                if field not in vals:
                    continue

                field_obj = rec._fields.get(field)

                # MANY2ONE
                if field_obj and field_obj.type == 'many2one':

                    old_name = rec[field].display_name if rec[field] else '-'

                    new_record = self.env[field_obj.comodel_name].browse(vals[field]) if vals[field] else False
                    new_name = new_record.display_name if new_record else '-'

                    if old_name != new_name:
                        changes.append((field, old_name, new_name))

                # NORMAL FIELD
                else:
                    old_name = rec[field] or '-'
                    new_name = vals[field] or '-'

                    if old_name != new_name:
                        changes.append((field, old_name, new_name))

            if changes:
                email_changes_map[rec.id] = changes

        res = super(SoftwareAsset, self).write(vals)

        for rec in self:
            changes = email_changes_map.get(rec.id)

            if changes:
                rows = ""
                for field, old, new in changes:
                    rows += f"""
                        <tr>
                            <td>{rec._fields[field].string}</td>
                            <td>{old}</td>
                            <td>{new}</td>
                        </tr>
                    """

                rec._send_mail_to_followers(
                    subject="Software License Updated",
                    body=f"""
                        <p><b>Software:</b> {rec.name}</p>
                        <table border="1" cellpadding="5">
                            <tr>
                                <th>Field</th>
                                <th>Old</th>
                                <th>New</th>
                            </tr>
                            {rows}
                        </table>
                    """
                )

        return res

    def check_software_expiry(self):

        today = fields.Date.today()

        records = self.search([('expiry_date', '!=', False)])

        for rec in records:

            delta = (rec.expiry_date - today).days

            notify_days = [60, 30, 15, 7, 1]

            if delta in notify_days or delta < 0:
                status = "Expired" if delta < 0 else f"Expires in {delta} days"

                rec._send_mail_to_followers(
                    subject="Software Expiry Alert",
                    body=f"""
                            <div style="font-family: Arial, sans-serif; font-size: 14px;">

                                <p>Hello,</p>

                                <p>
                                    This is to inform you that the following software license requires attention:
                                </p>

                                <table style="border-collapse: collapse; margin-top: 10px;">
                                    <tr>
                                        <td style="padding: 6px 12px;"><b>Software Name</b></td>
                                        <td style="padding: 6px 12px;">{rec.name}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 6px 12px;"><b>Expiry Date</b></td>
                                        <td style="padding: 6px 12px;">{rec.expiry_date or '-'}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 6px 12px;"><b>Status</b></td>
                                        <td style="padding: 6px 12px; color: {'red' if 'Expired' in status else '#d48806'};">
                                            <b>{status}</b>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin-top: 15px;">
                                    Kindly take the necessary action to renew or review this license.
                                </p>

                                <p>
                                    Regards,<br/>
                                    <b>Inventory Management System</b>
                                </p>

                            </div>
                        """
                )


class SoftwareLicenseType(models.Model):
    _name = 'software.license.type'
    _description = 'Software License Type'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char(string="License Type", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    description = fields.Text(string="Description")



class SoftwareInstallation(models.Model):
    _name = 'software.installation'
    _description = 'Software Installation'

    software_id = fields.Many2one('software.asset', string="Software", required=True, ondelete='cascade')
    device = fields.Many2one('custom.inventory', string="Installed On Device", required=True)
    installed_by = fields.Many2one('hr.employee', string="Installed By")
    install_date = fields.Date(string="Installation Date", default=fields.Date.context_today)
    remarks = fields.Text(string="Remarks")
    model_id = fields.Many2one(
        'inventory.model',
        string="Device Model",
        tracking=True
    )


class SoftwareRenewal(models.Model):
    _name = 'software.renewal'
    _description = 'Software Renewal History'
    _order = 'renewal_date desc'

    software_id = fields.Many2one('software.asset', string="Software", required=True, ondelete='cascade')
    renewal_date = fields.Date(string="Renewal Date", required=True)
    renewed_by = fields.Many2one('hr.employee', string="Renewed By")
    amount = fields.Float(string="Amount")
    remarks = fields.Text(string="Remarks")
