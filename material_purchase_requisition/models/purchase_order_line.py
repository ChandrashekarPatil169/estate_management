from odoo import fields, models,api


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    alternative_group = fields.Char(
        string="Alternative Group",
        help="Group alternative quotation options from the same vendor",tracking=True
    )

    specification = fields.Text(string="Specification")
    technical_remarks = fields.Text(string="Technical Remarks")



    # SCORES
    eval_price_score = fields.Float("Price %",tracking=True)
    eval_qty_score = fields.Float("Quantity %",tracking=True)
    eval_delivery_score = fields.Float("Delivery %",tracking=True)
    eval_discount_score = fields.Float("Discount %",tracking=True)
    eval_total_score = fields.Float("Total %",tracking=True)

    # FOR REPORT
    vendor_id = fields.Many2one(
        related="order_id.partner_id",
        string="Vendor",
        store=True,
        tracking=True
    )

    delivery_date = fields.Datetime(
        related="order_id.date_planned",
        string="Delivery Date",
        store=True,
        tracking=True
    )

    is_best_vendor = fields.Boolean("Best Vendor",tracking=True)