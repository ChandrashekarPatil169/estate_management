from odoo import models, fields, _
from odoo.exceptions import AccessError, ValidationError

class ProjectRejectWizard(models.TransientModel):
    _name = 'project.reject.wizard'
    _description = 'Project Reject Wizard'

    project_id = fields.Many2one(
        'project.project',
        required=True,
        readonly=True
    )

    reject_reason = fields.Text(
        string="Reason for Rejection",
        required=True
    )

    def action_confirm_reject(self):
        self.ensure_one()
        project = self.project_id

        if project.state != 'draft':
            raise ValidationError(_("Only Draft projects can be rejected."))

        if not project.is_current_user_approver:
            raise AccessError(_("You are not allowed to reject this project."))

        project.write({
            'state': 'rejected',
            'reject_reason': self.reject_reason,
        })

        # 2. Trigger the Email
        template = self.env.ref('project_hierarchy_management.mail_template_project_rejected', raise_if_not_found=False)
        if template:
            # Gather recipients: Project Manager + Followers who have an email
            partner_ids = project.message_follower_ids.mapped('partner_id').filtered(lambda p: p.email).ids
            if project.user_id.partner_id.email:
                partner_ids.append(project.user_id.partner_id.id)

            # Use set() to remove duplicates, then back to list
            partner_ids = list(set(partner_ids))

            if partner_ids:
                # Add 'recipient_ids' to email_values so 'To (Partners)' is filled
                template.with_context(rejected_by=self.env.user.name).send_mail(
                    project.id,
                    force_send=True,
                    email_values={'recipient_ids': [(6, 0, partner_ids)]}
                )

        # Optional: log in chatter
        project.message_post(
            body=_(
                "Project Rejected\n"
                "Reason: %s"
            ) % self.reject_reason
        )

        return {'type': 'ir.actions.act_window_close'}
