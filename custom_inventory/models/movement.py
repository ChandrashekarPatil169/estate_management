from odoo import models, fields, api
from odoo.exceptions import ValidationError

class InventoryMovement(models.Model):
    _name = 'inventory.movement'
    _description = 'Asset Movement History'
    _order = 'date desc'
    _rec_name = 'reference'
    _inherit = ['mail.thread']

    # ================= MAIN =================
    movement_line_ids = fields.One2many(
        'inventory.movement.line',
        'movement_id',
        string="Assets"
    )
    reference = fields.Char(
        string="Movement Reference",
        readonly=True,
        copy=False,
        index=True
    )


    reason = fields.Char()
    date = fields.Datetime(default=fields.Datetime.now)

    # ================= MODE =================
    is_internal = fields.Boolean("Internal")
    is_external = fields.Boolean("External")

    # ================= INTERNAL =================
    from_location_id = fields.Many2one('inventory.location')
    to_location_id = fields.Many2one('inventory.location')
    from_warehouse_id = fields.Many2one(
        'inventory.warehouse',
        string="From Warehouse",
        tracking=True,
        domain=lambda self: [
            ('id', 'in',
             self.env.user.warehouse_exec_ids.ids +
             self.env.user.warehouse_manager_ids.ids)
        ]
    )

    to_warehouse_id = fields.Many2one(
        'inventory.warehouse',
        string="To Warehouse",
        tracking=True,
        domain=lambda self: [
            ('id', 'in',
             self.env.user.warehouse_exec_ids.ids +
             self.env.user.warehouse_manager_ids.ids)
        ]
    )
    from_employee_id = fields.Many2one('hr.employee')
    to_employee_id = fields.Many2one('hr.employee')

    from_address = fields.Text()
    to_address = fields.Text()

    # ================= EXTERNAL =================
    partner_id = fields.Many2one('res.partner')
    external_address = fields.Text()

    # PRINT BUTTON
    def action_print(self):
        return self.env.ref('custom_inventory.report_inventory_movement_action').report_action(self)

    @api.constrains('is_internal', 'is_external')
    def _check_movement_type(self):
        for rec in self:
            if rec.is_internal and rec.is_external:
                raise ValidationError("Movement cannot be both Internal and External at the same time.")
            if not rec.is_internal and not rec.is_external:
                raise ValidationError("Please select either Internal or External movement.")

    def _validate_followers_against_warehouse(self, partners, vals=None):
        for record in self:

            # GET WAREHOUSES
            from_wh = record.from_warehouse_id
            to_wh = record.to_warehouse_id

            # HANDLE CREATE / WRITE VALUES
            if vals:
                if vals.get('from_warehouse_id'):
                    from_wh = self.env['inventory.warehouse'].browse(vals['from_warehouse_id'])
                if vals.get('to_warehouse_id'):
                    to_wh = self.env['inventory.warehouse'].browse(vals['to_warehouse_id'])

            for partner in partners:
                user = partner.user_ids[:1]

                if not user:
                    continue

                allowed_warehouses = (
                        user.warehouse_exec_ids.ids +
                        user.warehouse_manager_ids.ids
                )

                # ✅ FLEXIBLE LOGIC (OR CONDITION)
                is_allowed = False

                if from_wh and from_wh.id in allowed_warehouses:
                    is_allowed = True

                if to_wh and to_wh.id in allowed_warehouses:
                    is_allowed = True

                # ❌ THROW ERROR ONLY IF BOTH FAIL
                if not is_allowed:
                    raise ValidationError(
                        f"{user.name} is not assigned to either FROM warehouse "
                        f"'{from_wh.name if from_wh else '-'}' or TO warehouse "
                        f"'{to_wh.name if to_wh else '-'}'."
                    )

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        if partner_ids:
            partners = self.env['res.partner'].browse(partner_ids)

            # 🔥 VALIDATION
            self._validate_followers_against_warehouse(partners)

        return super().message_subscribe(
            partner_ids=partner_ids,
            subtype_ids=subtype_ids
        )

    def write(self, vals):

        if 'message_partner_ids' in vals:
            partner_ids = []

            for command in vals.get('message_partner_ids'):
                if command[0] == 4:
                    partner_ids.append(command[1])
                elif command[0] == 6:
                    partner_ids.extend(command[2])

            partners = self.env['res.partner'].browse(partner_ids)

            self._validate_followers_against_warehouse(partners, vals)

        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            vals['reference'] = self._generate_reference()

        records = super().create(vals_list)

        # 🔥 KEEP YOUR FOLLOWER LOGIC SAME
        for record, vals in zip(records, vals_list):
            if vals.get('message_partner_ids'):
                partner_ids = []

                for command in vals.get('message_partner_ids'):
                    if command[0] == 4:
                        partner_ids.append(command[1])
                    elif command[0] == 6:
                        partner_ids.extend(command[2])

                partners = self.env['res.partner'].browse(partner_ids)
                record._validate_followers_against_warehouse(partners, vals)

        return records

    def _generate_reference(self):
        prefix = "REF"

        # 🔥 GET LAST RECORD FROM DB (NOT MEMORY)
        last_record = self.search(
            [('reference', 'like', f'{prefix}%')],
            order='reference desc',
            limit=1
        )

        if last_record and last_record.reference:
            try:
                last_number = int(last_record.reference.replace(prefix, ''))
                new_number = last_number + 1
            except:
                new_number = 1
        else:
            new_number = 1

        return f"{prefix}{str(new_number).zfill(3)}"

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if rec.partner_id:
                rec.external_address = rec.partner_id.contact_address
            else:
                rec.external_address = False




class InventoryMovementLine(models.Model):
    _name = 'inventory.movement.line'
    _description = 'Movement Line'

    movement_id = fields.Many2one('inventory.movement', ondelete='cascade')

    inventory_id = fields.Many2one('custom.inventory', string="Asset Tag", required=True,domain="[('warehouse_id', '=', movement_warehouse_id)]")

    product_name_id = fields.Many2one('inventory.product', readonly=True)
    brand_id = fields.Many2one('inventory.brand', readonly=True)
    model_id = fields.Many2one('inventory.model', readonly=True)
    serial_no = fields.Char(readonly=True)
    part_no = fields.Char(readonly=True)
    movement_warehouse_id = fields.Many2one(
        'inventory.warehouse',
        related='movement_id.from_warehouse_id',
        store=True
    )

    @api.onchange('from_warehouse_id')
    def _onchange_warehouse(self):
        for rec in self:
            rec.movement_line_ids = [(5, 0, 0)]

    @api.onchange('inventory_id')
    def _onchange_inventory_id(self):
        for rec in self:
            if rec.inventory_id:
                inv = rec.inventory_id
                rec.product_name_id = inv.product_name_id.id
                rec.brand_id = inv.brand_id.id
                rec.model_id = inv.model_id.id
                rec.serial_no = inv.serial_no
                rec.part_no = inv.part
            else:
                rec.product_name_id = False
                rec.brand_id = False
                rec.model_id = False
                rec.serial_no = False
                rec.part_no = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('inventory_id'):
                inv = self.env['custom.inventory'].browse(vals['inventory_id'])
                vals.update({
                    'product_name_id': inv.product_name_id.id,
                    'brand_id': inv.brand_id.id,
                    'model_id': inv.model_id.id,
                    'serial_no': inv.serial_no,
                    'part_no': inv.part,
                })
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('inventory_id'):
            inv = self.env['custom.inventory'].browse(vals['inventory_id'])
            vals.update({
                'product_name_id': inv.product_name_id.id,
                'brand_id': inv.brand_id.id,
                'model_id': inv.model_id.id,
                'serial_no': inv.serial_no,
                'part_no': inv.part,
            })
        return super().write(vals)










