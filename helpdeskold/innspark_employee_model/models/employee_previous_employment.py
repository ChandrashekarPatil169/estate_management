from odoo import models, fields

class HrEmployeePreviousEmployment(models.Model):
    _name = 'hr.employee.previous.employment'
    _description = 'Previous Employment'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
    )
    company_name = fields.Char(string='Company Name', required=True, tracking=True)
    designation = fields.Char(string='Designation', tracking=True)
    duration = fields.Char(string='Duration', tracking=True)
    reason_for_leaving = fields.Text(string='Reason for Leaving', tracking=True)
