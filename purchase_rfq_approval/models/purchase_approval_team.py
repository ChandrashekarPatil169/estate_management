from odoo import models, fields

class PurchaseApprovalTeam(models.Model):
    _name = "purchase.approval.team"
    _description = "Purchase Approval Team"

    name = fields.Char(string="Team Name", required=True,tracking=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,tracking=True
    )

    rule_ids = fields.One2many(
        "purchase.approval.rule",
        "team_id",
        string="Approval Rules",tracking=True
    )
