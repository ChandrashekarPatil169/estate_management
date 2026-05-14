from odoo import models, fields

class EstateMaintenanceRequest(models.Model):
    _name = 'estate.maintenance.request'
    _description = 'Maintenance Request'
    _rec_name = "name"
    _order = "request_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']  # <-- enables followers & chatter

    name = fields.Char(string="Request Title", required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    request_date = fields.Date(string="Request Date", default=fields.Date.context_today, tracking=True)

    property_id = fields.Many2one('estate.property', string="Property", tracking=True)
    building_id = fields.Many2one('estate.building', string="Building", tracking=True)
    unit_id = fields.Many2one('estate.unit', string="Unit", tracking=True)
    room_id = fields.Many2one('estate.room', string="Room", tracking=True)

    assigned_to = fields.Many2one('res.users', string="Assigned To", tracking=True)
    vendor = fields.Char(string="External Vendor", tracking=True)
    cost_estimate = fields.Float(string="Cost Estimate", tracking=True)
    actual_cost = fields.Float(string="Actual Cost", tracking=True)

    status = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='new',
        string="Status",
        tracking=True
    )

    maintenance_type = fields.Selection(
        [
            ('repair', 'Repair'),
            ('cleaning', 'Cleaning'),
            ('painting', 'Painting'),
            ('pest_control', 'Pest Control'),
            ('other', 'Other'),
        ],
        string="Maintenance Type",
        tracking=True
    )

    schedule_date = fields.Date(string="Scheduled Date", tracking=True)
    completion_date = fields.Date(string="Completion Date", tracking=True)
