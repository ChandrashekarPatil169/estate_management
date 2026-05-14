from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class WorkSummaryService(models.Model):
    _name = 'work.summary.service'
    _description = 'Daily Work Summary Service'

    @api.model
    def _cron_daily_user_work_summary(self):

        today = fields.Date.today()

        # ✅ Get SMTP sender safely
        # mail_server = self.env['ir.mail_server'].search([], limit=1)
        # email_from = mail_server.smtp_user or 'odoo_master@innspark.in'
        email_from = self.env['ir.config_parameter'].sudo().get_param('mail.default.from') or self.env.company.email

        users = self.env['res.users'].search([
            ('active', '=', True),
            ('email', '!=', False)
        ])

        template = self.env.ref(
            'project_main_mgmt.email_template_daily_work_summary',
            raise_if_not_found=False
        )

        if not template:
            _logger.error("Missing daily summary template")
            return

        # ✅ FETCH ALL TASKS ONCE (IMPORTANT)
        all_tasks = self.env['project.task'].search([
            ('is_done', '=', False),
            ('planned_start_date', '<=', today),
            ('assignee_id', '!=', False),
        ])

        all_subtasks = self.env['project.subtask'].search([
            ('status', '!=', 'done'),
            ('planned_start_date', '<=', today),
            ('assignee_id', '!=', False),
        ])

        # ✅ GROUP BY USER (NO N+1)
        task_map = {}
        for t in all_tasks:
            task_map.setdefault(t.assignee_id.id, []).append(t)

        subtask_map = {}
        for s in all_subtasks:
            subtask_map.setdefault(s.assignee_id.id, []).append(s)

        for user in users:
            try:
                tasks = self.env['project.task'].browse(
                    [t.id for t in task_map.get(user.id, [])]
                )
                subtasks = self.env['project.subtask'].browse(
                    [s.id for s in subtask_map.get(user.id, [])]
                )

                if not tasks and not subtasks:
                    continue

                # ✅ SPLIT LOGIC
                overdue_tasks = tasks.filtered(
                    lambda t: t.planned_end_date and t.planned_end_date < today
                )
                upcoming_tasks = tasks - overdue_tasks

                overdue_subtasks = subtasks.filtered(
                    lambda s: s.planned_end_date and s.planned_end_date < today
                )
                upcoming_subtasks = subtasks - overdue_subtasks

                template.with_context(
                    user=user,
                    overdue_tasks=overdue_tasks,
                    upcoming_tasks=upcoming_tasks,
                    overdue_subtasks=overdue_subtasks,
                    upcoming_subtasks=upcoming_subtasks,
                ).send_mail(
                    user.id,
                    force_send=True,
                    email_values={
                        'email_to': user.email,
                        'email_from': email_from,  # ✅ Odoo automatically routes this to your 10 Priority Gmail server
                    }
                )
            except Exception:
                _logger.exception(f"Daily summary failed for user {user.id}")