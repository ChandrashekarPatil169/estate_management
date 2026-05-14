from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ReviewReminderService(models.Model):
    _name = 'review.reminder.service'
    _description = 'Review Reminder Service'

    @api.model
    def _cron_review_reminder(self):
        today = fields.Date.today()

        # 1. Get the 'From' address from System Parameters (Production Safe)
        # This avoids hardcoding and matches your SMTP login perfectly.
        from_filter = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.alias')
        mail_domain = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')

        # Fallback to the authorized outgoing server email if parameters aren't set
        default_from = f"{from_filter}@{mail_domain}" if from_filter and mail_domain else False
        if not default_from:
            mail_server = self.env['ir.mail_server'].search([], limit=1)
            default_from = mail_server.smtp_user if mail_server else False

        if not default_from:
            _logger.error("No authorized 'From' email found. Configure System Parameters or Mail Server.")
            return

        template_task = self.env.ref('project_main_mgmt.email_template_task_review_reminder', raise_if_not_found=False)
        template_subtask = self.env.ref('project_main_mgmt.email_template_subtask_review_reminder',
                                        raise_if_not_found=False)

        if not template_task or not template_subtask:
            _logger.error("Review reminder templates are missing in data files.")
            return

        # 2. Optimized Search (Odoo 19 uses 'state' for tasks by default)
        # Check if your custom module uses 'status' or standard Odoo 'state'
        tasks = self.env['project.task'].search([
            ('stage_id.name', 'ilike', 'review'),
            ('status', '!=', 'done'),
            '|',
            ('last_review_reminder_date', '=', False),
            ('last_review_reminder_date', '!=', today),
        ])

        # 3. Batch Email Processing
        for task in tasks:
            try:
                # Use mapped to get all emails at once
                # approvers = task.project_id.approver_ids or task.approver_ids
                approvers = False

                if hasattr(task, 'approver_ids') and task.approver_ids:
                    approvers = task.approver_ids
                elif hasattr(task.project_id, 'approver_ids'):
                    approvers = task.project_id.approver_ids

                if not approvers:
                    continue
                recipient_emails = ",".join(approvers.filtered(lambda a: a.email).mapped('email'))

                if recipient_emails:
                    template_task.send_mail(
                        task.id,
                        force_send=True,
                        email_values={
                            'email_to': recipient_emails,
                            'email_from': default_from,  # Dynamic from System Config
                        }
                    )
                    # Update date only on success
                    task.last_review_reminder_date = today

            except Exception as e:
                _logger.error(f"Failed to send task reminder for {task.id}: {str(e)}")

        # 4. Subtask Logic
        subtasks = self.env['project.subtask'].search([
            ('stage_id.name', 'ilike', 'review'),
            ('status', '!=', 'done'),
            '|',
            ('last_review_reminder_date', '=', False),
            ('last_review_reminder_date', '!=', today),
        ])

        for sub in subtasks:
            try:
                # approvers = sub.project_id.approver_ids or sub.approver_ids
                approvers = False

                if hasattr(task, 'approver_ids') and task.approver_ids:
                    approvers = task.approver_ids
                elif hasattr(task.project_id, 'approver_ids'):
                    approvers = task.project_id.approver_ids

                if not approvers:
                    continue
                recipient_emails = ",".join(approvers.filtered(lambda a: a.email).mapped('email'))

                if recipient_emails:
                    template_subtask.send_mail(
                        sub.id,
                        force_send=True,
                        email_values={
                            'email_to': recipient_emails,
                            'email_from': default_from,
                        }
                    )
                    sub.last_review_reminder_date = today
            except Exception as e:
                _logger.error(f"Failed to send subtask reminder for {sub.id}: {str(e)}")

# from odoo import models, fields, api
# import logging
#
# _logger = logging.getLogger(__name__)
#
#
# class ReviewReminderService(models.Model):
#     _name = 'review.reminder.service'
#     _description = 'Review Reminder Service'
#
#     @api.model
#     def _cron_review_reminder(self):
#
#         today = fields.Date.today()
#
#         mail_server = self.env['ir.mail_server'].search([], limit=1)
#         smtp_user = mail_server.smtp_user if mail_server else None
#
#         if not smtp_user:
#             _logger.error("SMTP not configured")
#             return
#
#         template_task = self.env.ref(
#             'project_main_mgmt.email_template_task_review_reminder',
#             raise_if_not_found=False
#         )
#
#         template_subtask = self.env.ref(
#             'project_main_mgmt.email_template_subtask_review_reminder',
#             raise_if_not_found=False
#         )
#
#         if not template_task or not template_subtask:
#             _logger.error("Templates missing")
#             return
#
#         tasks = self.env['project.task'].search([
#             ('stage_id.name', 'ilike', 'review'),
#             ('status', '!=', 'done'),
#             '|',
#             ('last_review_reminder_date', '=', False),
#             ('last_review_reminder_date', '!=', today),
#         ])
#
#         for task in tasks:
#             try:
#                 approvers = task.project_id.approver_ids or task.approver_ids
#                 partners = approvers.mapped('partner_id').filtered(lambda p: p.email)
#
#                 if not partners:
#                     continue
#
#                 emails = ','.join(partners.mapped('email'))
#
#                 template_task.sudo().send_mail(
#                     task.id,
#                     force_send=True,
#                     email_values={
#                         'email_to': emails,
#                         'email_from': smtp_user,
#                         'mail_server_id': mail_server.id,
#                     }
#                 )
#
#                 task.last_review_reminder_date = today
#
#             except Exception:
#                 _logger.exception(f"Task review reminder failed {task.id}")
#
#         # -------- SUBTASK --------
#         subtasks = self.env['project.subtask'].search([
#             ('stage_id.name', 'ilike', 'review'),
#             ('status', '!=', 'done'),
#             '|',
#             ('last_review_reminder_date', '=', False),
#             ('last_review_reminder_date', '!=', today),
#         ])
#
#         for sub in subtasks:
#             try:
#                 approvers = getattr(sub.project_id, 'approver_ids', False) or sub.approver_ids
#
#                 partners = approvers.mapped('partner_id').filtered(lambda p: p.email)
#
#                 if not partners:
#                     continue
#
#                 emails = ','.join(partners.mapped('email'))
#
#                 template_subtask.sudo().send_mail(
#                     sub.id,
#                     force_send=True,
#                     email_values={
#                         'email_to': emails,
#                         'email_from': smtp_user,
#                     }
#                 )
#
#                 sub.last_review_reminder_date = today
#
#             except Exception:
#                 _logger.exception(f"Subtask review reminder failed {sub.id}")
