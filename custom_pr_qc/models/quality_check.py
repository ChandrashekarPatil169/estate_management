from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MaterialQualityCheck(models.Model):
    _name = 'material.quality.check'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '3-Way Quality Check'

    picking_id = fields.Many2one('stock.picking', string="Receipt", readonly=True,tracking=True)
    pr_id = fields.Many2one('material.purchase.requisition', string="Origin PR", readonly=True,tracking=True)
    # Product Lines
    line_ids = fields.One2many(
        'material.quality.check.line',
        'qc_id',
        string="Products",tracking=True
    )

    requester_id = fields.Many2one('res.users', string="PR Requester", readonly=True,tracking=True)
    admin_1_id = fields.Many2one('res.users', string="Inventory Person", readonly=True,tracking=True)
    admin_2_id = fields.Many2one('res.users', string="Accounting Person", readonly=True,tracking=True)


    access_url = fields.Char(compute='_compute_access_url',tracking=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Completed')
    ], compute='_compute_state', store=True, tracking=True)

    @api.depends(
        'line_ids.req_result',
        'line_ids.inv_result',
        'line_ids.acc_result'
    )
    def _compute_state(self):
        for rec in self:
            all_done = all(
                l.req_result in ['pass', 'reject'] and
                l.inv_result in ['pass', 'reject'] and
                l.acc_result in ['pass', 'reject']
                for l in rec.line_ids
            )
            rec.state = 'done' if all_done else 'pending'




    # def _compute_access_url(self):
    #     # Fetches the base URL (e.g., http://localhost:8018)
    #     base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    #     for rec in self:
    #         # Standard Odoo backend URL structure
    #         rec.access_url = f"{base_url}/odoo/material.quality.check/{rec.id}"

        # ----------------------------------------
        # FETCH PRODUCTS FROM PICKING
        # ----------------------------------------

    @api.model
    def create(self, vals):
        rec = super().create(vals)

        if rec.picking_id:
            lines = []

            for move in rec.picking_id.move_ids:

                if move.product_uom_qty <= 0:
                    continue

                lines.append((0, 0, {
                    'product_id': move.product_id.id,
                    'qty': move.product_uom_qty
                }))

            rec.line_ids = lines

        return rec

    last_reminder_date = fields.Date()

    @api.model
    def _cron_qc_reminder(self):

        today = fields.Date.today()

        qcs = self.search([
            ('state', '=', 'pending')
        ])

        template = self.env.ref(
            'custom_pr_qc.email_template_qc_reminder',
            raise_if_not_found=False
        )

        if not template:
            return

        for qc in qcs:

            # جلوگیری duplicate same-day spam
            if qc.last_reminder_date == today:
                continue

            picking = qc.picking_id
            if not picking:
                continue

            pending_users = []

            for line in qc.line_ids:

                if line.req_result == 'pending':
                    pending_users.append(qc.requester_id)

                if line.inv_result == 'pending':
                    pending_users.append(qc.admin_1_id)

                if line.acc_result == 'pending':
                    pending_users.append(qc.admin_2_id)

            pending_users = list(set(pending_users))

            partner_ids = [
                u.partner_id.id
                for u in pending_users
                if u and u.partner_id and u.partner_id.email
            ]

            if not partner_ids:
                continue

            picking.message_post_with_source(
                template,
                subtype_xmlid="mail.mt_comment",
                partner_ids=partner_ids
            )

            qc.last_reminder_date = today



        # ----------------------------------------
        # DIRECT LINK

    product_names = fields.Char(
        string="Products",
        compute="_compute_product_names",tracking=True
    )

    def _compute_product_names(self):
        for rec in self:
            products = rec.line_ids.mapped('product_id.name')
            rec.product_names = ", ".join(products)


    # ----------------------------------------

    def _compute_access_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            rec.access_url = f"{base_url}/odoo/material.quality.check/{rec.id}"


class MaterialQualityCheckLine(models.Model):
    _name = 'material.quality.check.line'
    _description = 'QC Product Lines'

    qc_id = fields.Many2one('material.quality.check',tracking=True)

    product_id = fields.Many2one('product.product', string="Product",tracking=True)
    qty = fields.Float(string="Quantity",tracking=True)

    # Individual Checker Approval
    req_result = fields.Selection([
        ('pending', 'Pending'),
        ('pass', 'Pass'),
        ('reject', 'Reject')
    ], default='pending',tracking=True)

    inv_result = fields.Selection([
        ('pending', 'Pending'),
        ('pass', 'Pass'),
        ('reject', 'Reject')
    ], default='pending',tracking=True)

    acc_result = fields.Selection([
        ('pending', 'Pending'),
        ('pass', 'Pass'),
        ('reject', 'Reject')
    ], default='pending',tracking=True)

    # ----------------------------------------
    # PASS BUTTON
    # ----------------------------------------
    def action_pass(self):
        for rec in self:


            user = self.env.user
            qc = rec.qc_id

            if user == qc.requester_id:
                rec.req_result = 'pass'

            elif user == qc.admin_1_id:
                rec.inv_result = 'pass'

            elif user == qc.admin_2_id:
                rec.acc_result = 'pass'

            else:
                raise UserError("You are not assigned checker.")

        # ----------------------------------------
        # REJECT BUTTON
        # ----------------------------------------

    def action_reject(self):
        for rec in self:

            user = self.env.user
            qc = rec.qc_id

            # ----------------------------
            # Identify checker role
            # ----------------------------
            if user == qc.requester_id:
                rec.req_result = 'reject'
                checker_role = "Requester"

            elif user == qc.admin_1_id:
                rec.inv_result = 'reject'
                checker_role = "Inventory"

            elif user == qc.admin_2_id:
                rec.acc_result = 'reject'
                checker_role = "Accounts"

            else:
                raise UserError("You are not assigned checker.")

            # ----------------------------
            # Remove quantity
            # ----------------------------
            rec.qty = 0

            picking = qc.picking_id

            moves = picking.move_ids.filtered(
                lambda m: m.product_id.id == rec.product_id.id
            )

            for move in moves:
                for line in move.move_line_ids:
                    line.quantity = 0

            # ----------------------------
            # CHATTER MESSAGE
            # ----------------------------
            qc.message_post(
                body=f"""
                    Product Rejected
                    Product: {rec.product_id.display_name}
                    Rejected By: {user.name}({checker_role})
                """
            )

