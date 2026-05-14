from odoo import models, api
from ..utils.html_security import to_safe_html, to_safe_email
from markupsafe import Markup, escape

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def message_post(self, **kwargs):
        body = kwargs.get('body')
        subtype = kwargs.get('subtype_xmlid')

        print("\n========== LOG NOTE DEBUG START ==========")
        print("Model:", self._name)
        print("Record ID:", self.id)
        print("Subtype:", subtype)
        print("\n--- ORIGINAL BODY ---\n", body)

        if subtype == 'mail.mt_note' and body:
            escaped_body = escape(body)
            safe_body = Markup(f"<pre>{escaped_body}</pre>")

            kwargs['body'] = safe_body

            print("\n--- ESCAPED BODY ---\n", escaped_body)
            print("\n--- FINAL BODY SENT TO ODOO ---\n", safe_body)
        else:
            print("\n--- NO TRANSFORMATION APPLIED ---")

        print("========== LOG NOTE DEBUG END ==========\n")

        return super().message_post(**kwargs)


















#PERFECT ONE

# from odoo import models, api
# from markupsafe import Markup
# from odoo.tools import html_sanitize
#
# class MailFollowers(models.Model):
#     _inherit = "mail.followers"
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         followers = super().create(vals_list)
#
#         Mail = self.env['mail.mail']
#
#         for follower in followers:
#
#             # ✅ Skip anything that is not CRM Opportunity
#             if follower.res_model != 'crm.lead':
#                 continue
#
#             if follower.partner_id.email:
#
#                 lead = self.env['crm.lead'].browse(follower.res_id)
#
#                 body = f"""
#                 <p><b>You have been added as a follower for an Opportunity.</b></p>
#
#                 <p>The following opportunity has been shared with you for tracking and updates:</p>
#
#                 <table border="0" cellpadding="4" cellspacing="0">
#                 <tr>
#                     <td><b>Opportunity</b></td>
#                     <td>: {lead.opportunity_ref or lead.name}</td>
#                 </tr>
#                 <tr>
#                     <td><b>Customer</b></td>
#                     <td>: {lead.partner_id.name or '-'}</td>
#                 </tr>
#                 </table>
#
#                 <br/>
#
#                 <p>Please review the opportunity details in the CRM system.</p>
#
#                 <p>
#                 Regards,<br/>
#                 <b>{self.env.company.name}</b>
#                 </p>
#                 """
#
#                 # Email
#                 Mail.create({
#                     'subject': 'Added as Follower - Opportunity',
#                     'body_html': body,
#                     # 'body_html': f"<pre>{body}</pre>",
#                     'email_to': follower.partner_id.email,
#                     'email_from': self.env.company.email,
#                     'auto_delete': False,
#                 }).send()
#
#                 # Chatter message
#                 lead.message_post(
#                     body=Markup(body),
#                     subject="Added as Follower - Opportunity",
#                     subtype_xmlid="mail.mt_comment",
#                 )
#
#         return followers