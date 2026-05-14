from odoo import models, fields


class AlternativeRFQConfirmWizard(models.TransientModel):
    _name = "material.alternative.rfq.confirm.wizard"

    _description = "Alternative RFQ Confirmation"

    po_id = fields.Many2one(
        "purchase.order",
        string="Selected RFQ",
        readonly=True,
        required=True,
        tracking=True
    )

    alternative_rfq_ids = fields.Many2many(
        "purchase.order",
        string="Alternative RFQs",
        readonly=True,
        tracking=True
    )

    decision = fields.Selection(
        [
            ("keep", "Confirm and keep alternatives"),
            ("cancel", "Confirm and cancel alternatives"),
        ],
        default="cancel",
        required=True,
        tracking=True
    )

    def action_confirm(self):
        self.ensure_one()

        # Confirm chosen RFQ
        self.po_id.with_context(
            skip_alternative_check=True
        ).button_confirm()

        # Cancel others if chosen
        if self.decision == "cancel":
            self.alternative_rfq_ids.button_cancel()

        return {"type": "ir.actions.act_window_close"}
