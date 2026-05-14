from odoo import models
import logging
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super().action_post()

        for rec in self:

            # 🔥 ONLY for vendor bills (expenses)
            if rec.move_type != 'in_invoice':
                continue

            followers = rec.message_partner_ids

            if not followers:
                continue

            rec.sudo().message_post(
                body=f"""
                    <b>✅ Expense Paid</b><br/>
                    Bill: <b>{rec.name}</b><br/>
                    Vendor: <b>{rec.partner_id.name}</b><br/>
                    Amount: <b>{rec.amount_total}</b>
                """,
                partner_ids=followers.ids,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )

        return res


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def action_create_payments(self):
        payments = super().action_create_payments()

        active_ids = self.env.context.get('active_ids', [])
        _logger.error("🔥 ACTIVE IDS: %s", active_ids)

        move_lines = self.env['account.move.line'].browse(active_ids)
        moves = move_lines.mapped('move_id')
        _logger.error("🔥 MOVES: %s", moves)

        for move in moves:
            _logger.error("🔥 MOVE: %s", move.name)

            expense = self.env['hr.expense'].search([
                ('account_move_id', '=', move.id)
            ], limit=1)
            _logger.error("🔥 EXPENSE: %s", expense)

            if not expense or not expense.travel_request_id:
                _logger.error("❌ NO EXPENSE OR TRAVEL REQUEST — SKIPPING")
                continue

            travel = expense.travel_request_id
            _logger.error("🔥 TRAVEL: %s", travel.name)

            amount_paid_on_bill = move.amount_total - move.amount_residual
            _logger.error("🔥 BILL TOTAL: %s | RESIDUAL: %s | PAID: %s",
                          move.amount_total, move.amount_residual, amount_paid_on_bill)
            _logger.error("🔥 CURRENT TRAVEL PAID_AMOUNT: %s", travel.paid_amount)

            new_payment = self.amount
            travel.sudo().write({
                'paid_amount': travel.paid_amount + new_payment
            })
            _logger.error("✅ UPDATED TRAVEL PAID_AMOUNT TO: %s", travel.paid_amount)
        return payments

