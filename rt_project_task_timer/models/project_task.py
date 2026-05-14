from odoo import models, fields, api,_
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import datetime


class ProjectTask(models.Model):
    # _inherit = ['project.task', 'timer.engine']
    _inherit = 'project.task'

    task_order = fields.Integer(
        string='Order',
        default=10,
        help='Order field used to organize tasks'
    )

    task_start_date = fields.Datetime(
        string='Start Date',
        default=fields.Datetime.now,
        copy=False,
        help='Date and time when the task was created'
    )

    task_end_date = fields.Datetime(
        string='End Date',
        copy=False,
        help='Date and time when the task was moved to a completed stage'
    )

    task_accumulated_time = fields.Integer(
        string='Accumulated Time (seconds)',
        default=0,
        help='Total accumulated time since the task was created',
        copy=False
    )

    timer_running = fields.Boolean(
        string='Timer Running',
        default=False,
        copy=False,
        help='Indicates whether the timer is currently running'
    )

    task_accumulated_time_realtime = fields.Integer(
        string='Accumulated Time (Real-Time)',
        compute='_compute_realtime_accumulated_time',
        help='Accumulated time updated in real time',
        store=False
    )

    task_timer = fields.Char(
        string='Task Timer',
        compute='_compute_task_timer',
        store=False,
        help='Technical field used to display the timer widget'
    )

    task_timer_color = fields.Selection([
        ('green', 'Green - Less than 1 hour'),
        ('yellow', 'Yellow - Between 1 and 2 hours'),
        ('red', 'Red - More than 2 hours'),
    ], string='Timer Color', compute='_compute_task_timer_color', store=False)

    is_concluded = fields.Boolean(
        string='Task Completed',
        compute='_compute_is_concluded',
        store=True,
        help='True if the task is in a completed stage'
    )

    weightage = fields.Selection(
        [(str(i), str(i)) for i in range(1, 11)],
        string="Weightage",
    )

    timer_state = fields.Selection(
        [
            ('stopped', 'Stopped'),
            ('running', 'Running'),
            ('paused', 'Paused'),
        ],
        default='stopped',
        copy=False
    )

    # task_start_date = fields.Datetime(copy=False)
    # task_accumulated_time = fields.Integer(default=0, copy=False)

    # weightage = fields.Float(
    #     string="Weightage (%)",
    #     digits=(5, 2)
    # )

    employee_weightage_id = fields.Many2one(
        'hr.employee',
        string="Employee (Weightage Link)"
    )

    planned_date = fields.Date(
        string="Planned Date"
    )

    completed_date = fields.Date(
        string="Completed Date"
    )

    status_display = fields.Selection(
        [
            ('active', 'Active'),
            ('completed', 'Completed'),
        ],
        string="Status",
        compute="_compute_status_display",
        store=True,
    )

    @api.depends('is_concluded')
    def _compute_status_display(self):
        for rec in self:
            if rec.is_concluded:
                rec.status_display = 'completed'
            else:
                rec.status_display = 'active'
    # @api.depends('stage_id', 'stage_id.fold')
    # def _compute_status_display(self):
    #     for rec in self:
    #         if rec.stage_id and rec.stage_id.fold:
    #             rec.status_display = 'completed'
    #         else:
    #             rec.status_display = 'active'

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)

        if 'stage_id' in vals:
            for task in self:
                if task.stage_id and task.stage_id.fold:
                    if not task.completed_date:
                        task.completed_date = fields.Date.today()

        return res

    # @api.constrains('weightage')
    # def _check_weightage(self):
    #     for rec in self:
    #         if rec.weightage < 0 or rec.weightage > 100:
    #             raise ValidationError("Weightage must be between 0 and 100.")

    @api.depends('task_start_date', 'task_accumulated_time', 'timer_running')
    def _compute_realtime_accumulated_time(self):
        for task in self:
            if task.timer_running and task.task_start_date:
                now_utc = fields.Datetime.now()
                elapsed = (now_utc - task.task_start_date).total_seconds()
                task.task_accumulated_time_realtime = int(
                    task.task_accumulated_time + elapsed
                )
            else:
                task.task_accumulated_time_realtime = task.task_accumulated_time

    # @api.depends('task_start_date', 'task_accumulated_time', 'timer_running')
    # def _compute_realtime_accumulated_time(self):
    #     """Calculate accumulated time in real time using UTC"""
    #     for task in self:
    #         if task.timer_running and task.task_start_date:
    #             now_utc = fields.Datetime.now()
    #             elapsed = (now_utc - task.task_start_date).total_seconds()
    #             task.task_accumulated_time_realtime = int(task.task_accumulated_time + elapsed)
    #         else:
    #             task.task_accumulated_time_realtime = task.task_accumulated_time

    @api.depends('task_accumulated_time_realtime')
    def _compute_task_timer(self):
        """Technical field for the timer widget"""
        for task in self:
            task.task_timer = str(task.task_accumulated_time_realtime)

    @api.depends('task_accumulated_time_realtime')
    def _compute_task_timer_color(self):
        """Calculate timer color based on real-time accumulated time"""
        ICP = self.env['ir.config_parameter'].sudo()
        yellow_hours = float(ICP.get_param('rt_project_task_timer.yellow_hours', '1.0'))
        red_hours = float(ICP.get_param('rt_project_task_timer.red_hours', '2.0'))

        for task in self:
            hours = task.task_accumulated_time_realtime / 3600.0  # Convert seconds to hours

            if hours >= red_hours:
                task.task_timer_color = 'red'
            elif hours >= yellow_hours:
                task.task_timer_color = 'yellow'
            else:
                task.task_timer_color = 'green'

    @api.depends('stage_id', 'stage_id.fold')
    def _compute_is_concluded(self):
        """Determine whether the task is in a completed stage"""
        for task in self:
            task.is_concluded = bool(task.stage_id and task.stage_id.fold)

    @api.model_create_multi
    def create(self, vals_list):
        """Set start date but DO NOT start timer automatically"""
        for vals in vals_list:
            if 'task_start_date' not in vals:
                vals['task_start_date'] = fields.Datetime.now()

            # Ensure timer is NOT running by default
            if 'timer_running' not in vals:
                vals['timer_running'] = False

        return super(ProjectTask, self).create(vals_list)

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
                rec.timer_running = True  # 🔥 REQUIRED FOR LIVE TIMER

    def action_pause_timer(self):
        self._check_timesheet_timer_access()
        for rec in self:
            if rec.timer_state != 'running':
                continue

            now = fields.Datetime.now()
            seconds = int((now - rec.task_start_date).total_seconds())

            rec.task_accumulated_time += seconds
            rec.timer_state = 'paused'
            rec.timer_running = False  # 🔥 REQUIRED

    def action_stop_timer(self):
        self._check_timesheet_timer_access()
        for rec in self:

            if rec.timer_state == 'running':
                now = fields.Datetime.now()
                seconds = int((now - rec.task_start_date).total_seconds())
                rec.task_accumulated_time += seconds

            if rec.task_accumulated_time <= 0:
                rec.timer_state = 'stopped'
                rec.timer_running = False  # 🔥 REQUIRED
                return

            hours = rec.task_accumulated_time / 3600.0

            # 🔥 DESCRIPTION FORMAT YOU WANT
            description = f"{rec.project_id.name} - {rec.name}"

            # self.env['account.analytic.line'].create({
            #     'project_id': rec.project_id.id,
            #     'task_id': rec.id,
            #     'employee_id': self.env.user.employee_id.id,
            #     'unit_amount': hours,
            #     'name': description,
            # })
            self.env['account.analytic.line'].with_context(
                from_timer_create=True
            ).create({
                'project_id': rec.project_id.id,
                'task_id': rec.id,
                'account_id': rec.project_id.account_id.id,
                'employee_id': self.env.user.employee_id.id,
                'unit_amount': hours,
                'name': description,
            })

            # Reset timer
            rec.task_accumulated_time = 0
            rec.timer_state = 'stopped'
            rec.timer_running = False  # 🔥 REQUIRED
            rec.task_start_date = False

    # def action_start_timer(self):
    #     for rec in self:
    #         if rec.timer_state in ('stopped', 'paused'):
    #             rec.task_start_date = fields.Datetime.now()
    #             rec.timer_state = 'running'
    #
    # def action_pause_timer(self):
    #     for rec in self:
    #         if rec.timer_state != 'running':
    #             continue
    #
    #         now = fields.Datetime.now()
    #         seconds = int((now - rec.task_start_date).total_seconds())
    #
    #         rec.task_accumulated_time += seconds
    #         rec.timer_state = 'paused'
    #
    # def action_stop_timer(self):
    #     for rec in self:
    #
    #         if rec.timer_state == 'running':
    #             now = fields.Datetime.now()
    #             seconds = int((now - rec.task_start_date).total_seconds())
    #             rec.task_accumulated_time += seconds
    #
    #         if rec.task_accumulated_time <= 0:
    #             rec.timer_state = 'stopped'
    #             return
    #
    #         hours = rec.task_accumulated_time / 3600.0
    #
    #         # 🔥 DESCRIPTION FORMAT YOU WANT
    #         description = f"{rec.project_id.name} - {rec.name}"
    #
    #         self.env['account.analytic.line'].create({
    #             'project_id': rec.project_id.id,
    #             'task_id': rec.id,
    #             'employee_id': self.env.user.employee_id.id,
    #             'unit_amount': hours,
    #             'name': description,
    #         })
    #
    #         # Reset timer
    #         rec.task_accumulated_time = 0
    #         rec.timer_state = 'stopped'
    #         rec.task_start_date = False
    # def action_start_timer(self):
    #     for task in self:
    #         if not task.timer_running and not task.is_concluded:
    #             task.write({
    #                 "task_start_date": fields.Datetime.now(),
    #                 "timer_running": True,
    #             })
    #     return True
    #
    # def action_stop_timer(self):
    #     for task in self:
    #         if not task.timer_running or not task.task_start_date:
    #             continue
    #
    #         now_utc = fields.Datetime.now()
    #         elapsed_seconds = int((now_utc - task.task_start_date).total_seconds())
    #
    #         if elapsed_seconds <= 0:
    #             continue
    #
    #         session_hours = elapsed_seconds / 3600.0
    #
    #         employee = self.env.user.employee_id
    #         if not employee:
    #             raise UserError("User not linked to employee.")
    #
    #         self.env["account.analytic.line"].create({
    #             "name": "",
    #             "date": fields.Date.today(),
    #             "employee_id": employee.id,
    #             "project_id": task.project_id.id,
    #             "task_id": task.id,
    #             "unit_amount": session_hours,
    #         })
    #
    #         task.write({
    #             "task_accumulated_time": 0,
    #             "timer_running": False,
    #             "task_start_date": False,
    #         })
    #
    #     return True

    # def action_start_timer(self):
    #     for task in self:
    #         if not task.timer_running and not task.is_concluded:
    #             task.task_start_date = fields.Datetime.now()
    #             task.timer_running = True
    #
    #
    #     return {
    #         "type": "ir.actions.client",
    #         "tag": "reload",
    #     }
    #
    # def action_stop_timer(self):
    #     for task in self:
    #         if not task.timer_running or not task.task_start_date:
    #             continue
    #
    #         now_utc = fields.Datetime.now()
    #         elapsed_seconds = int((now_utc - task.task_start_date).total_seconds())
    #
    #         if elapsed_seconds <= 0:
    #             continue
    #
    #         session_hours = elapsed_seconds / 3600.0
    #
    #         employee = self.env.user.employee_id
    #         if not employee:
    #             raise UserError("User not linked to employee.")
    #
    #         self.env["account.analytic.line"].create({
    #             "name": "",
    #             "date": fields.Date.today(),
    #             "employee_id": employee.id,
    #             "project_id": task.project_id.id,
    #             "task_id": task.id,
    #             "unit_amount": session_hours,
    #         })
    #
    #         task.task_accumulated_time = 0
    #         task.timer_running = False
    #         task.task_start_date = False
    #
    #         if task.parent_id:
    #             task._update_parent_timesheet()
    #
    #
    #     return {
    #         "type": "ir.actions.client",
    #         "tag": "reload",
    #     }

    def _create_timesheet_line(self, hours):
        self.env['account.analytic.line'].create({
            'project_id': self.project_id.id,
            'task_id': self.id,
            'employee_id': self.env.user.employee_id.id,
            'unit_amount': hours,
        })

    @api.constrains('weightage', 'user_ids', 'is_concluded')
    def _check_employee_weightage_limit(self):
        for task in self:

            # Skip if no weightage or no users
            if not task.weightage or not task.user_ids:
                continue

            task_weight = int(task.weightage)

            for user in task.user_ids:
                employee = user.employee_id
                if not employee:
                    continue

                # Get all ACTIVE main tasks assigned to this user
                tasks = self.search([
                    ('id', '!=', task.id),
                    ('parent_id', '=', False),  # Only main tasks
                    ('user_ids', 'in', user.id),
                    ('weightage', '!=', False),
                    ('is_concluded', '=', False),
                ])

                total_weight = sum(int(t.weightage) for t in tasks)

                # Add current task weight
                total_weight += task_weight

                if total_weight > 100:
                    raise ValidationError(
                        f"{employee.name} has reached maximum active weightage (100). "
                        f"Reduce weightage or complete some tasks first."
                    )



    # def action_start_timer(self):
    #     for task in self:
    #         if not task.timer_running and not task.is_concluded:
    #             task.task_start_date = fields.Datetime.now()
    #             task.timer_running = True
    #
    # def action_stop_timer(self):
    #     for task in self:
    #         if not task.timer_running or not task.task_start_date:
    #             continue
    #
    #         now_utc = fields.Datetime.now()
    #
    #         elapsed_seconds = int(
    #             (now_utc - task.task_start_date).total_seconds()
    #         )
    #
    #         if elapsed_seconds <= 0:
    #             continue
    #
    #         session_hours = elapsed_seconds / 3600.0
    #
    #         employee = self.env.user.employee_id
    #         if not employee:
    #             raise UserError(
    #                 "Your user is not linked to an employee. Please contact administrator."
    #             )
    #
    #         # 🔹 Create subtask timesheet line
    #         self.env["account.analytic.line"].create({
    #             "name": "",
    #             "date": fields.Date.today(),
    #             "employee_id": employee.id,
    #             "project_id": task.project_id.id,
    #             "task_id": task.id,
    #             "unit_amount": session_hours,
    #         })
    #
    #         # 🔴 Reset timer
    #         task.task_accumulated_time = 0
    #         task.timer_running = False
    #         task.task_start_date = False
    #
    #         # 🟢 NEW LOGIC — Update Parent Task
    #         if task.parent_id:
    #             task._update_parent_timesheet()

    # def action_stop_timer(self):
    #     for task in self:
    #         if not task.timer_running or not task.task_start_date:
    #             continue
    #
    #         now_utc = fields.Datetime.now()
    #
    #         # Calculate THIS session only
    #         elapsed_seconds = int(
    #             (now_utc - task.task_start_date).total_seconds()
    #         )
    #
    #         if elapsed_seconds <= 0:
    #             continue
    #
    #         session_hours = elapsed_seconds / 3600.0
    #
    #         # 🔹 Logged-in user's employee
    #         employee = self.env.user.employee_id
    #         if not employee:
    #             raise UserError(
    #                 "Your user is not linked to an employee. Please contact administrator."
    #             )
    #
    #         # 🔹 Create ONE timesheet line for this session
    #         self.env["account.analytic.line"].create({
    #             "name": "",  # empty description
    #             "date": fields.Date.today(),
    #             "employee_id": employee.id,
    #             "project_id": task.project_id.id,
    #             "task_id": task.id,
    #             "unit_amount": session_hours,
    #         })
    #
    #         # 🔴 RESET TIMER COMPLETELY
    #         task.task_accumulated_time = 0
    #         task.timer_running = False
    #         task.task_start_date = False

    # def action_stop_timer(self):
    #     for task in self:
    #         if not task.timer_running or not task.task_start_date:
    #             continue
    #
    #         now_utc = fields.Datetime.now()
    #
    #         # Calculate session elapsed seconds
    #         elapsed_seconds = int(
    #             (now_utc - task.task_start_date).total_seconds()
    #         )
    #
    #         if elapsed_seconds <= 0:
    #             continue
    #
    #         # Convert to hours (timesheets use hours)
    #         session_hours = elapsed_seconds / 3600.0
    #
    #         # Update accumulated time
    #         task.task_accumulated_time += elapsed_seconds
    #         task.timer_running = False
    #
    #         # 🔹 Get assignee's employee
    #         user = task.user_ids[:1]  # first assigned user
    #         if not user or not user.employee_id:
    #             raise UserError("The assigned user does not have a linked employee.")
    #
    #         employee = user.employee_id
    #
    #         # 🔹 Create timesheet line
    #         self.env["account.analytic.line"].create({
    #             "name": "",  # empty description
    #             "date": fields.Date.today(),
    #             "employee_id": employee.id,
    #             "project_id": task.project_id.id,
    #             "task_id": task.id,
    #             "unit_amount": session_hours,
    #         })
    # self.env["account.analytic.line"].create({
    #     "name": f"Timer entry - {task.name}",
    #     "date": fields.Date.today(),
    #     "employee_id": employee.id,
    #     "project_id": task.project_id.id,
    #     "task_id": task.id,
    #     "unit_amount": session_hours,
    # })

    # def action_stop_timer(self):
    #     for task in self:
    #         if task.timer_running and task.task_start_date:
    #             now_utc = fields.Datetime.now()
    #             elapsed = (now_utc - task.task_start_date).total_seconds()
    #             task.task_accumulated_time += int(elapsed)
    #             task.timer_running = False

    def action_sync_timer(self, seconds):
        """Called from JS when stopping timer"""
        self.ensure_one()
        self.task_accumulated_time = int(seconds)
        self.timer_running = False

    # @api.model_create_multi
    # def create(self, vals_list):
    #     """Set start date and start timer when creating the task"""
    #     for vals in vals_list:
    #         if 'task_start_date' not in vals:
    #             vals['task_start_date'] = fields.Datetime.now()
    #         if 'timer_running' not in vals:
    #             vals['timer_running'] = True
    #     return super(ProjectTask, self).create(vals_list)

    # def write(self, vals):
    #     """Detect when a task moves to a completed stage and stop the timer"""
    #     for task in self:
    #         if task.timer_running and task.task_start_date and 'stage_id' in vals:
    #             now_utc = fields.Datetime.now()
    #             elapsed = (now_utc - task.task_start_date).total_seconds()
    #             total_time = int(task.task_accumulated_time + elapsed)
    #
    #             vals['task_accumulated_time'] = total_time
    #             vals['task_start_date'] = now_utc
    #
    #     res = super(ProjectTask, self).write(vals)
    #
    #     if 'stage_id' in vals:
    #         for task in self:
    #             if task.is_concluded:
    #                 if task.timer_running:
    #                     task.timer_running = False
    #                 if not task.task_end_date:
    #                     task.task_end_date = fields.Datetime.now()
    #             elif not task.is_concluded and task.task_end_date:
    #                 task.timer_running = True
    #                 task.task_start_date = fields.Datetime.now()
    #                 task.task_end_date = False
    #
    #     return res

    def get_task_timer_hours(self):
        """Return accumulated time in hours (used in views)"""
        self.ensure_one()
        return self.task_accumulated_time / 3600.0

    def _update_parent_timesheet(self):

        self.ensure_one()

        # If called from project.task (native subtask)
        parent = self.parent_id

        if not parent:
            return

        # 🔹 Recalculate total hours for that parent task
        analytic_lines = self.env["account.analytic.line"].search([
            ("task_id", "=", parent.id)
        ])

        total_hours = sum(analytic_lines.mapped("unit_amount"))

        if total_hours <= 0:
            return

        # 🔹 Update or create summary line
        parent_line = self.env["account.analytic.line"].search([
            ("task_id", "=", parent.id),
            ("name", "=", "Subtasks Total")
        ], limit=1)

        if parent_line:
            parent_line.unit_amount = total_hours
        else:
            self.env["account.analytic.line"].create({
                "name": "Subtasks Total",
                "date": fields.Date.today(),
                "employee_id": self.env.user.employee_id.id,
                "project_id": parent.project_id.id,
                "task_id": parent.id,
                "unit_amount": total_hours,
            })

    # 27/2/2026
    # def _update_parent_timesheet(self):
    #     """
    #     Recalculate total timesheet of all subtasks
    #     and update/create one analytic line on parent task
    #     """
    #     self.ensure_one()
    #
    #     parent = self.parent_id
    #     if not parent:
    #         return
    #
    #     # 🔹 Get all subtasks of this parent
    #     subtasks = parent.child_ids
    #
    #     # 🔹 Sum all subtask analytic lines
    #     analytic_lines = self.env["account.analytic.line"].search([
    #         ("task_id", "in", subtasks.ids)
    #     ])
    #
    #     total_hours = sum(analytic_lines.mapped("unit_amount"))
    #
    #     if total_hours <= 0:
    #         return
    #
    #     # 🔹 Find existing parent summary line
    #     parent_line = self.env["account.analytic.line"].search([
    #         ("task_id", "=", parent.id),
    #         ("name", "=", "Subtasks Total")
    #     ], limit=1)
    #
    #     if parent_line:
    #         parent_line.unit_amount = total_hours
    #     else:
    #         self.env["account.analytic.line"].create({
    #             "name": "Subtasks Total",
    #             "date": fields.Date.today(),
    #             "employee_id": self.env.user.employee_id.id,
    #             "project_id": parent.project_id.id,
    #             "task_id": parent.id,
    #             "unit_amount": total_hours,
    #         })


# class AccountAnalyticLine(models.Model):
#     _inherit = "account.analytic.line"
#
#     task_level = fields.Integer(
#         compute="_compute_task_level",
#         store=True
#     )
#
#     @api.depends('task_id', 'task_id.parent_id')
#     def _compute_task_level(self):
#         for rec in self:
#             level = 0
#             task = rec.task_id
#             while task and task.parent_id:
#                 level += 1
#                 task = task.parent_id
#             rec.task_level = level
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    weightage = fields.Selection(
        [(str(i), str(i)) for i in range(1, 11)],
        string="Weightage",
    )


    task_ids = fields.Many2many(
        'project.task',
        compute='_compute_employee_tasks',
        string="Tasks",
        store=False
    )
    subtask_ids = fields.Many2many(
        'project.subtask',
        compute='_compute_employee_tasks',
        string="Subtasks",
        store=False
    )
    status_filter = fields.Selection(
        [
            ('all', 'All'),
            ('active', 'Active'),
            ('completed', 'Completed')
        ],
        string="Status Filter",
        default='all'
    )


    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")

    @api.depends('user_id', 'date_from', 'date_to', 'status_filter')
    def _compute_employee_tasks(self):

        for rec in self:

            if not rec.user_id:
                rec.task_ids = False
                rec.subtask_ids = False
                continue

            task_domain = [
                ('parent_id', '=', False),
                ('user_ids', 'in', rec.user_id.id),

                # REQUIRED FIELDS
                ('planned_start_date', '!=', False),
                ('planned_end_date', '!=', False),
                ('weightage', '!=', False),
                ('status_display', '!=', False),
            ]

            # Date filters
            if rec.date_from:
                task_domain.append(('planned_start_date', '>=', rec.date_from))

            if rec.date_to:
                task_domain.append(('planned_start_date', '<=', rec.date_to))

            # Status filter
            if rec.status_filter == 'active':
                task_domain.append(('status_display', '=', 'active'))

            elif rec.status_filter == 'completed':
                task_domain.append(('status_display', '=', 'completed'))

            tasks = self.env['project.task'].search(task_domain)

            # Subtask domain
            subtask_domain = [
                ('task_id', 'in', tasks.ids),

                # REQUIRED FIELDS
                ('planned_start_date', '!=', False),
                ('planned_end_date', '!=', False),
                ('subtask_weightage', '!=', False),
            ]

            subtasks = self.env['project.subtask'].search(subtask_domain)

            rec.task_ids = tasks
            rec.subtask_ids = subtasks


