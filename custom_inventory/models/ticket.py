from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Ticket(models.Model):
    _name = 'ticket.ticket'
    _description = 'Support Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string="Ticket Number",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('ticket.ticket')
    )
    subject = fields.Char(string="Subject", required=True, tracking=True)
    description = fields.Text(string="Description")

    priority = fields.Selection(
        [('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        string="Priority",
        default='medium',
        tracking=True
    )
    status = fields.Selection(
        [('new', 'New'), ('in_progress', 'In Progress'), ('on_hold', 'On Hold'),
         ('resolved', 'Resolved'), ('closed', 'Closed')],
        string="Status",
        default='new',
        tracking=True
    )

    # 🔗 Asset links
    inventory_id = fields.Many2one('custom.inventory', string="Related Inventory")
    software_id = fields.Many2one('software.asset', string="Related Software")

    # Auto-related fields from inventory
    asset_tag = fields.Char(related="inventory_id.asset_tag", string="Asset Tag", store=True, readonly=True)
    asset_type_id = fields.Many2one(related="inventory_id.asset_type_id", string="Asset Type", store=True, readonly=True)
    asset_category_id = fields.Many2one(related="inventory_id.asset_category_id", string="Asset Category", store=True, readonly=True)
    product_name_id = fields.Many2one(related="inventory_id.product_name_id", string="Product Name", store=True, readonly=True)
    brand_id = fields.Many2one(related="inventory_id.brand_id", string="Brand", store=True, readonly=True)
    model_id = fields.Many2one(related="inventory_id.model_id", string="Model", store=True, readonly=True)

    # 👤 Assignment
    reported_by = fields.Many2one('hr.employee', string="Reported By", tracking=True)
    assigned_to = fields.Many2one('hr.employee', string="Assigned To", tracking=True)

    # 📅 Dates
    assign_date = fields.Datetime(string="Assigned Date", readonly=True)
    resolve_date = fields.Datetime(string="Resolved Date", readonly=True)
    close_date = fields.Datetime(string="Closed Date", readonly=True)

    resolution_notes = fields.Text(string="Resolution Notes")
    cost = fields.Float(string="Resolution Cost")

    # 🔄 Override create
    def create(self, vals):
        """Set assign_date automatically when ticket is created with assigned_to"""
        if vals.get('assigned_to'):
            vals['assign_date'] = fields.Datetime.now()
        return super().create(vals)

    # 🔄 Override write
    def write(self, vals):
        """Auto-update assign_date, resolve_date, close_date based on changes"""
        for rec in self:
            # Assigned_to change
            if 'assigned_to' in vals and vals['assigned_to']:
                vals['assign_date'] = fields.Datetime.now()

            # Status change
            if 'status' in vals:
                if vals['status'] == 'resolved':
                    vals['resolve_date'] = fields.Datetime.now()
                elif vals['status'] == 'closed':
                    vals['close_date'] = fields.Datetime.now()

        return super().write(vals)

    # ✅ Actions
    def action_resolve(self):
        """Mark ticket as resolved"""
        for rec in self:
            rec.write({
                'status': 'resolved',
                'resolve_date': fields.Datetime.now()
            })

    def action_close(self):
        """Mark ticket as closed"""
        for rec in self:
            rec.write({
                'status': 'closed',
                'close_date': fields.Datetime.now()
            })
