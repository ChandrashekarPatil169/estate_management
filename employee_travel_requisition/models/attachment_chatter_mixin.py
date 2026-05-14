from odoo import models
from markupsafe import Markup


class AttachmentChatterMixin(models.AbstractModel):
    _name = 'attachment.chatter.mixin'
    _description = 'Attachment Chatter Mixin'

    def _post_line_attachments_to_chatter(self, model_name, line_label_func):
        for rec in self:
            if not getattr(rec, 'travel_id', False):
                continue

            attachments = self.env['ir.attachment'].search([
                ('res_model', '=', model_name),
                ('res_id', '=', rec.id)
            ])

            existing = rec.travel_id.message_ids.mapped('attachment_ids').ids

            for att in attachments:
                if att.id in existing:
                    continue

                new_attachment = att.copy({
                    'res_model': 'travel.request',
                    'res_id': rec.travel_id.id,
                })

                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>📎 Attachment Added</b><br/>
                        {att.name}<br/>
                        <small>{line_label_func(rec)}</small>
                    """),
                    attachment_ids=[new_attachment.id],
                    subtype_xmlid="mail.mt_note"
                )