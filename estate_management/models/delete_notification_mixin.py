from odoo import models


class DeleteNotificationMixin(models.AbstractModel):
    _name = 'delete.notification.mixin'
    _description = 'Delete Notification Mixin'

    def unlink(self):

        Mail = self.env['mail.mail']

        for rec in self:

            # emails = []
            # for partner in rec.message_partner_ids:
            #     if partner.email:
            #         emails.append(partner.email)
            #
            # if not emails:
            #     continue
            # for partner in rec.message_partner_ids:
            #     if not partner.email:
            #         continue
            followers = self.env['mail.followers'].search([
                ('res_model', '=', rec._name),
                ('res_id', '=', rec.id)
            ])

            partners = followers.mapped('partner_id').filtered(lambda p: p.email)

            for partner in partners:

                body = f"""
                        <div style="font-family: Arial; font-size: 14px;">

                            <p>Hello {partner.name},</p>

                            <p>
                                The following record has been <b style="color:red;">deleted</b>:
                            </p>

                            <table style="margin-top:10px;">
                                <tr>
                                    <td><b>Name</b></td>
                                    <td>: {rec.display_name}</td>
                                </tr>
                                <tr>
                                    <td><b>Type</b></td>
                                    <td>: {rec._description}</td>
                                </tr>
                            </table>

                            <p style="margin-top:15px;">
                                This action was performed in the system.
                            </p>

                            <p>
                                Regards,<br/>
                                <b>{self.env.company.name}</b>
                            </p>

                        </div>
                    """

                Mail.create({
                    'subject': f"{rec._description} Deleted",
                    'body_html': body,
                    'email_to': partner.email,
                    'auto_delete': False,
                }).send()

        return super().unlink()