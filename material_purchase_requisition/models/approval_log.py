from odoo import fields, models


class MaterialPurchaseApprovalLog(models.Model):
    _name = "material.purchase.approval.log"

    _order = "create_date desc"

    requisition_id = fields.Many2one(
        "material.purchase.requisition", ondelete="cascade",tracking=True
    )
    user_id = fields.Many2one("res.users",tracking=True)
    action = fields.Selection(
        [("approved", "Approved"), ("rejected", "Rejected")],
        required=True,tracking=True
    )
    reason = fields.Text(
        string="Reason",tracking=True
    )