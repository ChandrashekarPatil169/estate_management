from odoo import models, fields

class PurchaseApprovalHistory(models.Model):
    _name = "purchase.approval.history"
    _description = "Purchase Approval History"
    _order = "create_date desc"

    order_id = fields.Many2one(
        "purchase.order",
        string="Purchase Order",
        required=True,
        ondelete="cascade",tracking=True
    )

    user_id = fields.Many2one(
        "res.users",
        string="Action By",
        required=True,tracking=True
    )

    action = fields.Selection(
        [
            ("submitted", "Submitted for Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        required=True,tracking=True
    )

    remark = fields.Text(string="Remarks",tracking=True)
