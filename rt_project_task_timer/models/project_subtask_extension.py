from odoo import models, fields,_
from odoo.exceptions import UserError


class ProjectSubtask(models.Model):
    _inherit = ['project.subtask', 'timer.engine']

    task_start_date = fields.Datetime(copy=False)
    task_end_date = fields.Datetime(copy=False)
    task_accumulated_time = fields.Integer(default=0, copy=False)
    task_timer = fields.Char(compute="_compute_task_timer")
    timer_state = fields.Selection(
        [
            ('stopped', 'Stopped'),
            ('running', 'Running'),
            ('paused', 'Paused'),
        ],
        default='stopped',
        copy=False
    )

    timesheet_ids = fields.One2many(
        'account.analytic.line',
        'subtask_id',
        string="Timesheets",
        # readonly=True
    )

    def _compute_task_timer(self):
        for rec in self:
            rec.task_timer = "00:00:00"

    def _create_timesheet_line(self, hours):
        self.env['account.analytic.line'].create({
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,      # parent task
            'subtask_id': self.id,           # 🔥 IMPORTANT
            'employee_id': self.env.user.employee_id.id,
            'unit_amount': hours,
            'name': f"Subtask: {self.name}",
        })

    def _check_timesheet_timer_access(self):
        if self.env.user.has_group('base.group_system'):
            return

        for rec in self:
            if rec.project_id and hasattr(rec.project_id, '_current_user_has_timesheet_access'):
                if not rec.project_id._current_user_has_timesheet_access():
                    raise UserError(_("You do not have Timesheet / Timer access for this project."))

    def action_start_timer(self):
        self._check_timesheet_timer_access()
        for rec in self:
            if rec.timer_state in ('stopped', 'paused'):
                rec.task_start_date = fields.Datetime.now()
                rec.timer_state = 'running'
                rec.timer_running = True

    def action_pause_timer(self):
        self._check_timesheet_timer_access()
        for rec in self:
            if rec.timer_state != 'running':
                continue

            now = fields.Datetime.now()
            seconds = int((now - rec.task_start_date).total_seconds())

            rec.task_accumulated_time += seconds
            rec.timer_state = 'paused'
            rec.timer_running = False

    def action_stop_timer(self):
        self._check_timesheet_timer_access()
        for rec in self:
            if rec.timer_state == 'running':
                now = fields.Datetime.now()
                seconds = int((now - rec.task_start_date).total_seconds())
                rec.task_accumulated_time += seconds

            if rec.task_accumulated_time <= 0:
                rec.timer_state = 'stopped'
                rec.timer_running = False
                return

            hours = rec.task_accumulated_time / 3600.0

            # # CREATE TIMESHEET ONLY ON FINAL STOP
            # self.env['account.analytic.line'].create({
            #     'project_id': rec.project_id.id,
            #     'task_id': rec.task_id.id,
            #     'subtask_id': rec.id,
            #     'employee_id': self.env.user.employee_id.id,
            #     'unit_amount': hours,
            #     'name': f"Subtask: {rec.name}",
            # })
            self.env['account.analytic.line'].with_context(
                from_timer_create=True
            ).create({
                'project_id': rec.project_id.id,
                'task_id': rec.task_id.id,
                'subtask_id': rec.id,
                'employee_id': self.env.user.employee_id.id,
                'unit_amount': hours,
                'name': f"Subtask: {rec.name}",
            })

            # RESET TIMER
            rec.task_accumulated_time = 0
            rec.timer_state = 'stopped'
            rec.timer_running = False
            rec.task_start_date = False

    # def action_start_timer(self):
    #     for rec in self:
    #         if not rec.timer_running:
    #             rec.task_start_date = fields.Datetime.now()
    #             rec.timer_running = True
    #
    # def action_stop_timer(self):
    #     for rec in self:
    #         if not rec.timer_running or not rec.task_start_date:
    #             continue
    #
    #         now = fields.Datetime.now()
    #         seconds = int((now - rec.task_start_date).total_seconds())
    #
    #         rec.task_accumulated_time += seconds
    #         rec.task_end_date = now
    #         rec.timer_running = False
    #
    #         hours = seconds / 3600.0
    #         rec._create_timesheet_line(hours)


# from odoo import models, fields
# from datetime import datetime
#
# class ProjectSubtask(models.Model):
#     _inherit = ['project.subtask', 'timer.engine']
#
#     task_start_date = fields.Datetime(copy=False)
#     task_end_date = fields.Datetime(copy=False)
#     task_accumulated_time = fields.Integer(default=0, copy=False)
#     task_timer = fields.Char(compute="_compute_task_timer")
#     timesheet_ids = fields.One2many(
#         'account.analytic.line',
#         'subtask_id',
#         string="Timesheets",
#         readonly=True
#     )
#
#     def _create_timesheet_line(self, hours):
#         self.env['account.analytic.line'].create({
#             'project_id': self.project_id.id,
#             'task_id': self.task_id.id,  # parent task
#             'subtask_id': self.id,  # NEW link
#             'employee_id': self.env.user.employee_id.id,
#             'unit_amount': hours,
#             'name': f"{self.name}",
#         })
#
#     def _compute_task_timer(self):
#         for rec in self:
#             rec.task_timer = "00:00:00"
#
#     def _create_timesheet_line(self, hours):
#         self.env['account.analytic.line'].create({
#             'project_id': self.project_id.id,
#             'task_id': self.task_id.id,
#             'employee_id': self.env.user.employee_id.id,
#             'unit_amount': hours,
#             'name': f"Subtask: {self.name}",
#         })
#
#     def action_start_timer(self):
#         for rec in self:
#             if not rec.timer_running:
#                 rec.task_start_date = fields.Datetime.now()
#                 rec.timer_running = True
#
#     def action_stop_timer(self):
#         for rec in self:
#             if not rec.timer_running or not rec.task_start_date:
#                 continue
#
#             now = fields.Datetime.now()
#             seconds = int((now - rec.task_start_date).total_seconds())
#
#             rec.task_accumulated_time += seconds
#             rec.task_end_date = now
#             rec.timer_running = False
#
#             hours = seconds / 3600.0
#             rec._create_timesheet_line(hours)
#
# # from odoo import models
# #
# #
# # class ProjectSubtask(models.Model):
# #     _inherit = ['project.subtask', 'timer.engine']
# #
# #     def _create_timesheet_line(self, hours):
# #         self.env['account.analytic.line'].create({
# #             'project_id': self.project_id.id,
# #             'task_id': self.task_id.id,
# #             'employee_id': self.env.user.employee_id.id,
# #             'unit_amount': hours,
# #             'name': f"Subtask: {self.name}",
# #         })