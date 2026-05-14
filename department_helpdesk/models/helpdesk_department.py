from odoo import models, fields

class HelpdeskDepartment(models.Model):
    _name = 'helpdesk.department'
    _description = 'Helpdesk Department'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'department_id',
        string="Tickets"
    )

    department_id = fields.Many2one(
        "helpdesk.department",
        string="Department",
    )

    name = fields.Char(required=True)
    code = fields.Char(required=True, unique=True)
    manager_id = fields.Many2one("hr.employee", string="Manager")
    active = fields.Boolean(default=True)