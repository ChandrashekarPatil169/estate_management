from odoo import models
import ast


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        res = super().action_send_mail()

        for wizard in self:

            if wizard.model != 'purchase.order':
                continue

            res_ids = wizard.res_ids or self.env.context.get('active_ids', [])

            # 🔥 FIX: normalize res_ids
            if isinstance(res_ids, str):
                try:
                    res_ids = ast.literal_eval(res_ids)
                except Exception:
                    res_ids = []

            if isinstance(res_ids, int):
                res_ids = [res_ids]

            res_ids = [int(i) for i in res_ids if str(i).isdigit()]

            if not res_ids:
                continue

            purchase_orders = self.env['purchase.order'].browse(res_ids)

            for po in purchase_orders:

                if not po or not po.exists() or not po.pr_id:
                    continue

                if po.rfq_synced_to_pr:
                    continue

                pr = po.pr_id

                template = self.env.ref(
                    'material_purchase_requisition.mail_template_rfq_sent',
                    raise_if_not_found=False
                )

                if not template:
                    continue

                partners = pr.message_partner_ids.filtered(lambda p: p.email)

                if not partners:
                    continue

                pr.with_context(
                    current_po_id=po.id
                ).message_post_with_source(
                    template,
                    subtype_xmlid="mail.mt_comment",
                    partner_ids=partners.ids
                )

                po.rfq_synced_to_pr = True

        return res







# from odoo import models,fields,api,_
#
# class MailMail(models.Model):
#     _inherit = 'mail.mail'
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         records = super().create(vals_list)
#
#         for mail in records:
#
#             # Only RFQ mails
#             if mail.model != 'purchase.order' or not mail.res_id:
#                 continue
#
#             po = self.env['purchase.order'].browse(mail.res_id)
#
#             # Safety checks
#             if not po.exists() or not po.pr_id:
#                 continue
#
#             pr = po.pr_id
#
#             # Load template
#             template = self.env.ref(
#                 'material_purchase_requisition.mail_template_rfq_sent',
#                 raise_if_not_found=False
#             )
#
#             if not template:
#                 continue
#
#             # ✅ IMPORTANT: pass RFQ in context
#             pr.with_context(current_po_id=po.id).message_post_with_source(
#                 template,
#                 subtype_xmlid="mail.mt_comment"
#             )
#
#         return records
#
