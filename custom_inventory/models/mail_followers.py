from odoo import models, api
from markupsafe import Markup


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        Mail = self.env['mail.mail']

        for rec in records:

            # ONLY for your inventory
            # if rec.res_model == 'custom.inventory' and rec.partner_id:
            # if rec.res_model in ['custom.inventory', 'software.asset'] and rec.partner_id:
            if rec.partner_id:

                # inventory = self.env['custom.inventory'].browse(rec.res_id)
                record = self.env[rec.res_model].browse(rec.res_id)
                partner = rec.partner_id

                body = f"""
                    <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">

                        <p>Hello {partner.name},</p>

                        <p>
                            You have been successfully added as a <b>follower</b> for the following record:
                        </p>

                        <table style="border-collapse: collapse; margin-top: 10px;">
                            <tr>
                                <td style="padding: 6px 12px;"><b>Record Name</b></td>
                                <td style="padding: 6px 12px;">{record.display_name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 12px;"><b>Type</b></td>
                                <td style="padding: 6px 12px;">{record._description}</td>
                            </tr>
                        </table>

                        <p style="margin-top: 15px;">
                            You will now receive updates related to this record.
                        </p>

                        <p>
                            Regards,<br/>
                            <b>{self.env.company.name}</b>
                        </p>

                    </div>
                """

                # ✅ EMAIL (will show in Technical → Emails)
                if partner.email:
                    mail = Mail.create({
                        'subject': 'Follower Added',
                        'body_html': body,
                        'email_to': partner.email,
                        'auto_delete': False,
                    })
                    mail.send()

                # ✅ CHATTER
                record.message_post(
                    subject="Follower Added",
                    body=Markup(body),
                    message_type='comment',
                )

                record.invalidate_recordset() # ✅ ADD THIS LINE

        return records