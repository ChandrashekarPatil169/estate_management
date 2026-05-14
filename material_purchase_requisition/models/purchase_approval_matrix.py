from odoo import models, fields

class PurchaseApprovalMatrix(models.Model):
    _name = 'purchase.approval.matrix'

    _description = 'Purchase Approval Matrix'
    _order = 'min_amount asc'

    name = fields.Char(required=True)
    min_amount = fields.Monetary(required=True)
    max_amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True,tracking=True
    )
    approver_ids = fields.Many2many(
        'res.users',
        string='Additional Approvers',tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True,tracking=True
    )
