from odoo import models, fields
class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    # invoice_progress = fields.Float(string="Invoice Progress", compute="_compute_invoice_progress", store=True)

    rating_ids = fields.One2many(
        'employee.report',
        'employee_id',
        string="Ratings", tracking=True
    )

