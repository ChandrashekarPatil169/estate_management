from odoo import models, fields, _
from odoo.exceptions import UserError

class ProjectCharterRejectWizard(models.TransientModel):
    _name = 'project.charter.reject.wizard'
    _description = 'Project Charter Reject Wizard'

    project_id = fields.Many2one('project.project', string="Project")
    reason = fields.Text(string="Rejection Reason", required=True)

    def action_confirm_reject(self):
        self.ensure_one()

        if not self.project_id:
            raise UserError("Project not found.")

        project = self.project_id

        # -----------------------------
        # 1. Update state
        # -----------------------------
        project.write({
            'charter_state': 'rejected',
            'rejection_reason': self.reason,
        })

        # -----------------------------
        # 2. Get recipients (choose ONE)
        # -----------------------------

        # OPTION A → Followers
        partners = project.message_partner_ids.filtered(lambda p: p.email)

        # OPTION B → Approvers (better)
        # partners = project.charter_approval_line_ids.mapped(
        #     'user_id.partner_id'
        # ).filtered(lambda p: p.email)

        if not partners:
            raise UserError("No recipients with valid email.")

        # -----------------------------
        # 3. Send email USING TEMPLATE
        # -----------------------------
        # template = self.env.ref(
        #     'project_tabs.mail_template_project_rejected',
        #     raise_if_not_found=False
        # )
        #
        # if not template:
        #     raise UserError("Mail template not found.")
        #
        # # ✅ CRITICAL LINE (most devs miss this)
        # template.send_mail(
        #     project.id,
        #     email_values={
        #         'recipient_ids': [(6, 0, partners.ids)]
        #     },
        #     force_send=False
        # )

        template = self.env.ref(
            'project_tabs.mail_template_project_rejected',
            raise_if_not_found=False
        )

        if not template:
            raise UserError("Mail template not found.")

        mail_server = self.env['ir.mail_server'].search([], limit=1)
        smtp_user = mail_server.smtp_user if mail_server else None

        emails = ",".join(partners.mapped('email'))

        if not emails:
            raise UserError("No valid email addresses found.")

        template.sudo().send_mail(
            project.id,
            force_send=True,  # 🔥 IMPORTANT
            email_values={
                'email_to': emails,  # 🔥 DIRECT EMAIL
                'email_from': smtp_user  # 🔥 REQUIRED FOR SMTP
            }
        )

        # -----------------------------
        # 4. Chatter log ONLY (no email)
        # -----------------------------
        # project.message_post(
        #     body=f"❌ Charter rejected.<br/><b>Reason:</b> {self.reason}",
        #     subtype_xmlid="mail.mt_note"
        # )

        return {'type': 'ir.actions.act_window_close'}

    # def action_confirm_reject(self):
    #     self.ensure_one()
    #
    #     if self.project_id:
    #         # Find the "Rejected" stage
    #         rejected_stage = self.env['project.project.stage'].search(
    #             [('name', '=', 'Rejected')],
    #             limit=1
    #         )
    #
    #         vals = {
    #             'charter_state': 'rejected',
    #             'rejection_reason': self.reason,
    #         }
    #
    #         # Sync kanban stage if found
    #         if rejected_stage:
    #             vals['stage_id'] = rejected_stage.id
    #
    #         self.project_id.write(vals)
    #
    #         # Log to chatter
    #         self.project_id.message_post(
    #             body=_("<b>Charter Rejected</b><br/><b>Reason:</b> %s") % self.reason,
    #         )
    #
    #     return {'type': 'ir.actions.act_window_close'}

# from odoo import models, fields
#
# class ProjectCharterRejectWizard(models.TransientModel):
#     _name = 'project.charter.reject.wizard'
#     _description = 'Project Charter Reject Wizard'
#
#     project_id = fields.Many2one('project.project')
#     reason = fields.Text(string="Rejection Reason", required=True)
#
#     def action_confirm_reject(self):
#         self.project_id.write({
#             'charter_state': 'rejected',
#             'rejection_reason': self.reason
#         })
