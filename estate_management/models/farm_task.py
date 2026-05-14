# farm_task.py
from odoo import models, fields

class EstateFarmTask(models.Model):
    _name = 'estate.farm.task'
    _description = 'Farm Task'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']  # <-- enable chatter & followers
    _order = "id desc"

    name = fields.Char(string="Task Name", required=True, tracking=True)
    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    crop_id = fields.Many2one('estate.crop.name', string="Crop",tracking=True)
    livestock_id = fields.Many2one('estate.livestock', string="Livestock",tracking=True)
    assigned_to = fields.Many2one('hr.employee', string="Assigned To",tracking=True)
    priority = fields.Selection([('high','High'),('medium','Medium'),('low','Low')], string="Priority", tracking=True)
    start_date = fields.Date(tracking=True)
    end_date = fields.Date(tracking=True)
    status = fields.Selection([('planned','Planned'),('in_progress','In Progress'),('done','Done')], string="Status", tracking=True)
    resources_used = fields.Text(tracking=True)
    cost_estimate = fields.Float(tracking=True)
    notes = fields.Text(tracking=True)

    # ✅ Add missing fields
    iot_integration = fields.Text(string="IoT Integration Data",tracking=True)
    environmental_metrics = fields.Text(string="Environmental Metrics",tracking=True)
