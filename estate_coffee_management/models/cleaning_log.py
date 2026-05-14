from odoo import models, fields


class CleaningLog(models.Model):
    _name = 'cleaning.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Machine Cleaning Log'
    _rec_name ="machine_id"
    _order = "id desc"

    machine_id = fields.Many2one(
        'coffee.machine',
        string="Machine",
        required=True,
        tracking=True
    )
    building_id = fields.Many2one(
        related='machine_id.building_id',
        string="Building",
        store=True,
        readonly=True,
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        tracking=True
    )
    date_time = fields.Datetime(
        string="Cleaning Date/Time",
        default=fields.Datetime.now,
        tracking=True
    )
    remarks = fields.Text(
        string="Remarks",
        tracking=True
    )
