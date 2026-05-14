from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    subtask_id = fields.Many2one(
        "project.subtask",
        string="Subtask",
        ondelete="cascade",
    )

    def _is_project_user_readonly_mode(self):
        return (
                self.env.user.has_group('project.group_project_user')
                and not self.env.user.has_group('base.group_system')
                and not self.env.user.has_group('project_main_mgmt.group_program_manager')
                and not self.env.user.has_group('project_main_mgmt.group_custom_project_manager')
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If created from subtask
            if vals.get('subtask_id'):
                subtask = self.env['project.subtask'].browse(vals['subtask_id'])

                if subtask.task_id and not vals.get('task_id'):
                    vals['task_id'] = subtask.task_id.id

                if subtask.project_id and not vals.get('project_id'):
                    vals['project_id'] = subtask.project_id.id

                # analytic account from project
                if subtask.project_id and subtask.project_id.account_id:
                    vals['account_id'] = subtask.project_id.account_id.id

            # If created from task
            elif vals.get('task_id') and not vals.get('project_id'):
                task = self.env['project.task'].sudo().browse(vals['task_id'])
                if task.project_id:
                    vals['project_id'] = task.project_id.id
                if task.project_id and task.project_id.account_id:
                    vals['account_id'] = task.project_id.account_id.id

            # Final validation
            if vals.get('project_id') and not vals.get('account_id'):
                project = self.env['project.project'].sudo().browse(vals['project_id'])
                if project.account_id:
                    vals['account_id'] = project.account_id.id
                else:
                    raise ValidationError(_(
                        "This project does not have an Analytic Account. "
                        "Please configure an Analytic Account on the project before adding timesheets."
                    ))

        return super().create(vals_list)

    def write(self, vals):

        # system timer-created lines
        if self.env.context.get('from_timer_create'):
            return super().write(vals)

        # admin
        if self.env.user.has_group('base.group_system'):
            if any(line.subtask_id for line in self):
                return super(AccountAnalyticLine, self.with_context(from_subtask_timesheet_edit=True)).write(vals)
            return super().write(vals)

        # normal project user readonly mode only
        if self._is_project_user_readonly_mode():
            if not self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'):
                raise AccessError(_("You do not have Timesheet access."))

            allowed_fields = {
                'name',
                # 'date',
                # 'employee_id',
                # 'project_id',
                # 'task_id',
                # 'subtask_id',
                # 'account_id',
            }

            technical_ok = {
                'write_date',
                'write_uid',
                '__last_update',
                'display_name',
            }

            if 'unit_amount' in vals:
                for line in self:
                    old_hours = line.unit_amount or 0.0
                    new_hours = vals.get('unit_amount') or 0.0
                    if old_hours != new_hours:
                        raise AccessError(_("You can edit only the Timesheet Description. Hours are read-only."))

            if 'amount' in vals:
                raise AccessError(_("You can edit only the Timesheet Description. Amount is read-only."))

            forbidden = (set(vals.keys()) - technical_ok) - allowed_fields - {'unit_amount'}

            if forbidden:
                print("TIMESHEET BLOCKED FIELDS:", forbidden)
                raise AccessError(
                    _("You can edit only the Timesheet Description. Hours and other fields are read-only."))

        # 🔥 force bypass for subtask inline edit
        if any(line.subtask_id for line in self):

            return super(AccountAnalyticLine, self.with_context(from_subtask_timesheet_edit=True)).write(vals)

        return super().write(vals)

    def unlink(self):
        if self.env.user.has_group('base.group_system'):
            return super().unlink()

        if self._is_project_user_readonly_mode():
            raise AccessError(_("You are not allowed to delete Timesheet entries."))

        return super().unlink()
