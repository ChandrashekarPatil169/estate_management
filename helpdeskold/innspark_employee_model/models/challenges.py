from odoo import models, fields

class EmployeeChallengeLine(models.Model):
    _name = 'employee.challenge.line'
    _description = 'Employee Challenge Line'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        ondelete='cascade'
    )

    challenge_id = fields.Many2one(
        'gamification.challenge',
        string='Challenge',
        required=True
    )

    start_date = fields.Date()
    end_date = fields.Date()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='draft')

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    challenge_line_ids = fields.One2many(
        'employee.challenge.line',
        'employee_id',
        string='Challenges'
    )
