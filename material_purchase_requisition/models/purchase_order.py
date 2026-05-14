from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    pr_id = fields.Many2one(
        "material.purchase.requisition",
        string="Purchase Requisition",
        readonly=True,
        ondelete="restrict",
        index=True,
        tracking=True
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Requested By",
        related="pr_id.employee_id",
        store=True,
        readonly=True,
        tracking=True
    )

    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        related="pr_id.department_id",
        store=True,
        readonly=True,
        tracking=True
    )

    # ⭐ ADD RECEIVED STATE
    state = fields.Selection(
        selection_add=[('received', 'Received')],
        group_expand="_expand_states",tracking=True
    )

    def write(self, vals):
        if 'state' in vals:
            for order in self:
                if order.state == 'purchase' and vals['state'] == 'draft':
                    raise UserError("You cannot move a confirmed PO back to RFQ.")
        return super().write(vals)

    def _expand_states(self, states, domain):
        return ['draft', 'sent', 'purchase', 'received', 'cancel']

    @api.depends(
        'state',
        'order_line.qty_received',
        'order_line.qty_invoiced',
        'order_line.product_qty',
    )
    def _compute_invoice_status(self):
        super()._compute_invoice_status()

        for order in self:
            if order.state in ('purchase', 'received'):

                if all(
                        line.qty_invoiced >= line.product_qty
                        for line in order.order_line
                ):
                    order.invoice_status = 'invoiced'

                elif any(line.qty_received > 0 for line in order.order_line):
                    order.invoice_status = 'to invoice'

                else:
                    order.invoice_status = 'no'

    def button_cancel(self):
        for po in self:
            if po.pr_id and po.pr_id.state not in ('received', 'rejected'):
                po.pr_id.write({'state': 'rejected'})

        return super().button_cancel()

    def button_confirm(self):

        self.ensure_one()

        # --- KEEP YOUR EXISTING WIZARD LOGIC ---
        if not self.env.context.get("skip_alternative_check"):
            if self.state == "draft" and self.pr_id:
                alternatives = self.search([
                    ("id", "!=", self.id),
                    ("pr_id", "=", self.pr_id.id),
                    ("state", "=", "draft"),
                ])

                if alternatives:
                    return {
                        "type": "ir.actions.act_window",
                        "name": "Confirm RFQ (Alternatives)",
                        "res_model": "material.alternative.rfq.confirm.wizard",
                        "view_mode": "form",
                        "target": "new",
                        "context": {
                            "default_po_id": self.id,
                            "default_alternative_rfq_ids": alternatives.ids,
                        },
                    }

            # --- ALWAYS CONFIRM PO ---
        res = super().button_confirm()

        # 🔴 THIS MUST ALWAYS RUN
        if self.pr_id:
            self.pr_id.state = "po_confirmed"

        return res

    products_display = fields.Char(
        string="Products",
        compute="_compute_products_display",
        store=False,tracking=True
    )

    def _compute_products_display(self):
        for po in self:
            po.products_display = ", ".join(
                po.order_line.mapped("product_id.display_name")
            )

    def action_open_vendor_evaluation_views(self):

        rfqs = self.filtered(lambda r: r.state in ("draft", "sent"))

        if len(rfqs) < 2:
            raise UserError("Select at least TWO RFQs.")

        lines = self.env["purchase.order.line"].search([
            ("order_id", "in", rfqs.ids),
            ("product_id", "!=", False),
        ])

        WEIGHT = 25

        for product in lines.mapped("product_id"):

            product_lines = lines.filtered(lambda l: l.product_id == product)

            if len(product_lines) < 2:
                continue

            # ---------------- BEST VALUES
            best_price = min(product_lines.mapped(
                lambda l: l.price_subtotal * l.product_uom_qty
            ))

            best_qty = max(product_lines.mapped("product_uom_qty"))

            best_discount = max(product_lines.mapped("discount"))

            best_delivery = min([
                                    seller.delay
                                    for line in product_lines
                                    for seller in line.product_id.seller_ids
                                    if seller.partner_id == line.order_id.partner_id
                                ] or [1])

            # Reset best vendor flag
            product_lines.write({"is_best_vendor": False})

            for line in product_lines:

                total_price = line.price_subtotal * line.product_uom_qty

                # PRICE SCORE
                line.eval_price_score = (
                    (best_price / total_price) * WEIGHT
                    if total_price else 0
                )

                # QUANTITY SCORE
                line.eval_qty_score = (
                    (line.product_uom_qty / best_qty) * WEIGHT
                    if best_qty else 0
                )

                # DISCOUNT SCORE
                if best_discount > 0:
                    line.eval_discount_score = (
                            (line.discount / best_discount) * WEIGHT
                    )
                else:
                    line.eval_discount_score = 0

                # DELIVERY SCORE
                vendor_delay = next(
                    (
                        seller.delay
                        for seller in line.product_id.seller_ids
                        if seller.partner_id == line.order_id.partner_id
                    ),
                    best_delivery
                )

                line.eval_delivery_score = (
                    (best_delivery / vendor_delay) * WEIGHT
                    if vendor_delay else 0
                )

                # TOTAL SCORE
                line.eval_total_score = round(
                    line.eval_price_score +
                    line.eval_qty_score +
                    line.eval_discount_score +
                    line.eval_delivery_score,
                    2
                )

            # Find highest score
            max_score = max(product_lines.mapped("eval_total_score"))

            # Highlight all vendors with highest score
            best_vendors = product_lines.filtered(
                lambda l: l.eval_total_score == max_score
            )

            best_vendors.write({"is_best_vendor": True})

        return {
            "type": "ir.actions.act_window",
            "name": "Product Vendor Evaluation",
            "res_model": "purchase.order.line",
            "view_mode": "list",
            "views": [(self.env.ref(
                "material_purchase_requisition.view_product_vendor_evaluation_list"
            ).id, "list")],
            "domain": [("id", "in", lines.ids)],
        }

    def action_print_vendor_evaluation(self):
        return self.env.ref(
            "material_purchase_requisition.action_product_vendor_evaluation_report"
        ).report_action(self)

    receipt_status = fields.Selection([
        ('none', 'Nothing Received'),
        ('partial', 'Partially Received'),
        ('full', 'Fully Received'),
    ], compute="_compute_receipt_status", store=True,tracking=True)

    @api.depends('order_line.qty_received', 'order_line.product_qty')
    def _compute_receipt_status(self):
        for order in self:
            if not order.order_line:
                order.receipt_status = 'none'
                continue

            total_ordered = sum(order.order_line.mapped('product_qty'))
            total_received = sum(order.order_line.mapped('qty_received'))

            if total_received == 0:
                order.receipt_status = 'none'
            elif total_received < total_ordered:
                order.receipt_status = 'partial'
            else:
                order.receipt_status = 'full'

    rfq_synced_to_pr = fields.Boolean(
        string="RFQ Synced to PR",
        default=False,
        copy=False,
        index=True
    )

    def button_draft(self):
        """
        Reset flag if RFQ is reset to draft.
        So resend will trigger PR notification again.
        """
        res = super().button_draft()
        self.write({'rfq_synced_to_pr': False})
        return res