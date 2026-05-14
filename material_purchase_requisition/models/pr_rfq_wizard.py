from odoo import models, fields, api
from odoo.exceptions import UserError


class MaterialPRRFQWizard(models.TransientModel):
    _name = "material.pr.rfq.wizard"

    _description = "PR → RFQ Vendor Selection"

    pr_id = fields.Many2one(
        "material.purchase.requisition",
        required=True,
        readonly=True,
        tracking=True
    )

    # Helper field – computed, not stored
    allowed_vendor_ids = fields.Many2many(
        "res.partner",
        compute="_compute_allowed_vendors",
        store=False,
        tracking=True
    )

    # Vendor selection restricted to product vendors
    vendor_ids = fields.Many2many(
        "res.partner",
        string="Vendors",
        domain="[('id', 'in', allowed_vendor_ids)]",
        required=True,
        tracking=True
    )

    # ---------------------------------------------------------
    # COMPUTE PRODUCT-RESPONSIBLE VENDORS (FIXED)
    # ---------------------------------------------------------
    @api.depends("pr_id.line_ids.product_id")
    def _compute_allowed_vendors(self):
        for wizard in self:
            if not wizard.pr_id:
                wizard.allowed_vendor_ids = False
                continue

            # 🔥 Take ALL vendors exactly as configured on product
            vendors = wizard.pr_id.line_ids.mapped(
                "product_id.seller_ids.partner_id"
            )

            if not vendors:
                raise UserError(
                    "No vendors are configured on the products in this Purchase Requisition."
                )

            wizard.allowed_vendor_ids = vendors

    # ---------------------------------------------------------
    # CREATE RFQs (UNCHANGED)
    # ---------------------------------------------------------
    def action_confirm_create_rfqs(self):
        self.ensure_one()

        if len(self.vendor_ids) < 2:
            raise UserError("Please select at least 2 vendors for RFQ.")

        PurchaseOrder = self.env["purchase.order"]
        rfqs = []

        for vendor in self.vendor_ids:
            po = PurchaseOrder.create({
                "partner_id": vendor.id,
                "company_id": self.pr_id.company_id.id,
                "origin": self.pr_id.name,
                "pr_id": self.pr_id.id,
                "order_line": [
                    (0, 0, {
                        "product_id": line.product_id.id,
                        "name": line.product_id.display_name,
                        "product_qty": line.quantity,
                        "product_uom_id": line.product_id.uom_id.id,
                        "price_unit": line.price_unit,
                        "date_planned": fields.Datetime.now(),
                        "specification": line.specification,
                    })
                    for line in self.pr_id.line_ids
                ],
            })

            # ✅ to get the pr followers in its rfq
            if self.pr_id.message_partner_ids:
                po.message_subscribe(
                    partner_ids=self.pr_id.message_partner_ids.ids
                )
            rfqs.append(po.id)

        self.pr_id.rfq_created = True

        action = self.env.ref("purchase.purchase_rfq").read()[0]
        action["domain"] = [("id", "in", rfqs)]
        return action


