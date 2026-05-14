from odoo import models, fields


class EmployeeReport(models.Model):
    _name = 'employee.report'
    _description = 'Employee Report'

    # name = fields.Char(string="Report Name", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    date = fields.Date(string="Date", default=fields.Date.today, tracking=True)

    # rating = fields.Float(string="Rating", default=0.0)

    rating = fields.Selection([
        ('1', 'Very Bad'),
        ('2', 'Bad'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent'),
    ], string="Rating", default='1', tracking=True)

    comments = fields.Text(string="Comments", tracking=True)

