from odoo import models, fields

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    project_id = fields.Many2one(
        'project.project',
        string="Project"
    )
