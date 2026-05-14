from odoo import models, fields, api


class EstatePaymentLogicMixin(models.AbstractModel):
    _name = "estate.payment.logic.mixin"
    _description = "Estate Payment Logic"


    # @api.onchange('due_date', 'payment_done_date')
    # def _onchange_payment_logic(self):

        # today = fields.Date.today()
        #
        # for rec in self:

            # # If payment completed → amount = 0
            # if rec.payment_done_date:
            #     rec.amount = 0
            #     return

            # # If overdue → double existing amount
            # if rec.due_date and rec.due_date < today and rec.amount:
            #     rec.amount = rec.amount * 2

# from odoo import models, fields, api
#
#
# class EstatePaymentLogicMixin(models.AbstractModel):
#     _name = "estate.payment.logic.mixin"
#     _description = "Estate Payment Logic"
#
#     @api.onchange('due_date', 'payment_done_date', 'product_id')
#     def _onchange_payment_logic(self):
#
#         today = fields.Date.today()
#
#         for rec in self:
#
#             # If payment completed → amount becomes zero
#             if rec.payment_done_date:
#                 rec.amount = 0
#                 continue
#
#             # If overdue → double amount
#             if rec.due_date and rec.due_date < today and rec.product_id:
#                 rec.amount = rec.product_id.list_price * 2
#
#             # Normal case
#             elif rec.product_id:
#                 rec.amount = rec.product_id.list_price