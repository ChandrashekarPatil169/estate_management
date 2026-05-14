from odoo import models, fields

class HrEmployeeEducation(models.Model):
    _name = 'hr.employee.education'
    _description = 'Employee Educational Background'
    _order = 'sequence, year_of_passing desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True, tracking=True
    )

    sequence = fields.Integer(default=10, tracking=True)

    education_level = fields.Selection([
        ('10th', '10th Board'),
        ('12th', '12th Board'),
        ('ug', 'Under Graduate'),
        ('pg', 'Post Graduate'),
        ('dr', 'Doctorate (DR)'),
        ('cert', 'Other Certification'),
    ], string="Education Level", required=True, tracking=True)

    institute_name = fields.Char(
        string="Board / College / University",
        required=True, tracking=True
    )

    field_of_study = fields.Char(
        string="Major / Field of Study", tracking=True
    )

    issuing_authority = fields.Char(
        string="Issuing Authority", tracking=True
    )

    year_of_passing = fields.Integer(
        string="Year of Passing / Completion", tracking=True
    )

    certificate_file = fields.Binary(
        string="Certificate",
        attachment=True, tracking=True
    )

    certificate_filename = fields.Char(
        string="File Name" , tracking=True
    )

