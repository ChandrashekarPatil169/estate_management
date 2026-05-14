from odoo import fields, models,api


class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"

    _description = "Purchase Requisition Line"

    requisition_id = fields.Many2one(
        "material.purchase.requisition", ondelete="cascade",tracking=True
    )

    product_id = fields.Many2one("product.product", required=True,tracking=True)
    quantity = fields.Float(required=True,tracking=True)
    specification = fields.Text(string="Specification")
    price_unit = fields.Monetary(tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        related="requisition_id.currency_id",
        store=True,tracking=True
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id:
                line.price_unit = 0.0
                return

            # ✅ Correct purchase cost field
            line.price_unit = line.product_id.standard_price
