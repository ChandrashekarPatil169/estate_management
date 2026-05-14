from odoo import models, fields


# =====================================================
# EXTEND EMPLOYEE
# =====================================================

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    training_ids = fields.One2many(
        'employee.training',
        'employee_id',
        string="Training Programs Attended"
    )

    language_ids = fields.One2many(
        'employee.language',
        'employee_id',
        string="Languages Known"
    )

    licence_ids = fields.One2many(
        'employee.licence',
        'employee_id',
        string="Licences / Permits"
    )

    promotion_ids = fields.One2many(
        'employee.promotion',
        'employee_id',
        string="Promotions and Transfers"
    )


# =====================================================
# TRAINING
# =====================================================

class EmployeeTraining(models.Model):
    _name = 'employee.training'
    _description = 'Employee Training'

    name = fields.Char("Training Name", required=True)
    provider = fields.Char("Provider")
    date = fields.Date("Date")

    employee_id = fields.Many2one(
        'hr.employee',
        required=True,
        ondelete='cascade'
    )


# =====================================================
# LANGUAGE
# =====================================================

class EmployeeLanguage(models.Model):
    _name = 'employee.language'
    _description = 'Employee Language'

    name = fields.Char("Language", required=True)

    proficiency = fields.Selection([
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('native', 'Native'),
    ], string="Proficiency")

    employee_id = fields.Many2one(
        'hr.employee',
        required=True,
        ondelete='cascade'
    )


# =====================================================
# LICENCE
# =====================================================

class EmployeeLicence(models.Model):
    _name = 'employee.licence'
    _description = 'Employee Licence'

    name = fields.Char("Licence / Permit", required=True)
    expiry_date = fields.Date("Expiry Date")

    employee_id = fields.Many2one(
        'hr.employee',
        required=True,
        ondelete='cascade'
    )


# =====================================================
# PROMOTION
# =====================================================

class EmployeePromotion(models.Model):
    _name = 'employee.promotion'
    _description = 'Employee Promotion'

    position = fields.Char("New Position")
    department = fields.Char("Department")
    effective_date = fields.Date("Effective Date")

    employee_id = fields.Many2one(
        'hr.employee',
        required=True,
        ondelete='cascade'
    )
