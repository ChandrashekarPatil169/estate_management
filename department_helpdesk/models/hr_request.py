from odoo import models, fields, api

class HrTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    department_type = fields.Selection([ ('facility', 'Facility Details'), ('it_incident', 'IT Incident'), ('inventory', 'Inventory and IT Assets'), ('hr', 'HR Department'), ], string="Department", tracking=True)

    hr_request_type_id = fields.Many2one(
        'helpdesk.hr.request.type',
        string="HR Request Type", tracking=True
    )

    grievance_policy = fields.Char(string="Grievance / Policy", tracking=True)
    incident_date = fields.Date(string="Incident Date", tracking=True)
    incident_location = fields.Char(string="Incident Location", tracking=True)

    people_ids = fields.Many2many(
        'hr.employee',
        'hr_ticket_employee_rel',
        'ticket_id',
        'employee_id',
        string="People Involved", tracking=True
    )

    confidential = fields.Boolean(string="Confidential", tracking=True)

    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        default=lambda self: self.env.user.employee_id.department_id.id if self.env.user.employee_id else False
    )


class HelpdeskHRRequestType(models.Model):
    _name = 'helpdesk.hr.request.type'
    _description = 'HR Request Type'
    _order = 'sequence, id'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)


