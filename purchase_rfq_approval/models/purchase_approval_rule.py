from odoo import models, fields
from odoo.exceptions import ValidationError

class PurchaseApprovalRule(models.Model):
    _name = "purchase.approval.rule"
    _description = "Purchase Approval Rule"
    _order = "sequence"

    team_id = fields.Many2one(
        "purchase.approval.team",
        required=True,
        ondelete="cascade",tracking=True
    )

    sequence = fields.Integer(default=10,tracking=True)

    min_amount = fields.Monetary(string="Minimum Amount", required=True,tracking=True)
    max_amount = fields.Monetary(string="Maximum Amount", required=True,tracking=True)

    approver_ids = fields.Many2many(
        "res.users",
        string="Approvers",
        required=True,tracking=True
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="team_id.company_id.currency_id",
        store=True,tracking=True
    )

    def _check_amount_range(self):
        for rec in self:
            if rec.min_amount >= rec.max_amount:
                raise ValidationError(
                    "Minimum amount must be less than maximum amount."
                )
