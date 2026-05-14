from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime


class ProjectTask(models.Model):
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
        help='Accumulated time updated in real time'
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

    @api.depends('task_start_date', 'task_accumulated_time', 'timer_running')
    def _compute_realtime_accumulated_time(self):
        """Calculate accumulated time in real time using UTC"""
        for task in self:
            if task.timer_running and task.task_start_date:
                now_utc = fields.Datetime.now()
                elapsed = (now_utc - task.task_start_date).total_seconds()
                task.task_accumulated_time_realtime = int(task.task_accumulated_time + elapsed)
            else:
                task.task_accumulated_time_realtime = task.task_accumulated_time

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
            task.is_concluded = task.stage_id and task.stage_id.fold

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

    def action_start_timer(self):
        for task in self:
            if not task.timer_running and not task.is_concluded:
                task.task_start_date = fields.Datetime.now()
                task.timer_running = True

    def action_stop_timer(self):
        for task in self:
            if not task.timer_running or not task.task_start_date:
                continue

            now_utc = fields.Datetime.now()

            # Calculate THIS session only
            elapsed_seconds = int(
                (now_utc - task.task_start_date).total_seconds()
            )

            if elapsed_seconds <= 0:
                continue

            session_hours = elapsed_seconds / 3600.0

            # 🔹 Logged-in user's employee
            employee = self.env.user.employee_id
            if not employee:
                raise UserError(
                    "Your user is not linked to an employee. Please contact administrator."
                )

            # 🔹 Create ONE timesheet line for this session
            self.env["account.analytic.line"].create({
                "name": "",  # empty description
                "date": fields.Date.today(),
                "employee_id": employee.id,
                "project_id": task.project_id.id,
                "task_id": task.id,
                "unit_amount": session_hours,
            })

            # 🔴 RESET TIMER COMPLETELY
            task.task_accumulated_time = 0
            task.timer_running = False
            task.task_start_date = False

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
# from odoo import models, fields, api
# from datetime import datetime
#
#
# class ProjectTask(models.Model):
#     _inherit = 'project.task'
#
#     task_order = fields.Integer(
#         string='Orden',
#         default=10,
#         help='Campo de orden para organizar las tareas'
#     )
#
#     task_start_date = fields.Datetime(
#         string='Fecha de Inicio',
#         default=fields.Datetime.now,
#         copy=False,
#         help='Fecha y hora de creación de la tarea'
#     )
#
#     task_end_date = fields.Datetime(
#         string='Fecha de Finalización',
#         copy=False,
#         help='Fecha y hora cuando la tarea se movió a una fase de conclusión'
#     )
#
#     task_accumulated_time = fields.Integer(
#         string='Tiempo Acumulado (segundos)',
#         default=0,
#         help='Tiempo total acumulado desde que se creó la tarea',
#         copy=False
#     )
#
#     timer_running = fields.Boolean(
#         string='Temporizador Activo',
#         default=False,
#         copy=False,
#         help='Indica si el temporizador está corriendo actualmente'
#     )
#
#     task_accumulated_time_realtime = fields.Integer(
#         string='Tiempo Acumulado en Tiempo Real',
#         compute='_compute_realtime_accumulated_time',
#         help='Tiempo acumulado actualizado en tiempo real'
#     )
#
#     task_timer = fields.Char(
#         string='Temporizador de Tarea',
#         compute='_compute_task_timer',
#         store=False,
#         help='Campo técnico para mostrar el widget del temporizador'
#     )
#
#     task_timer_color = fields.Selection([
#         ('green', 'Verde - Menos de 1 hora'),
#         ('yellow', 'Amarillo - Entre 1 y 2 horas'),
#         ('red', 'Rojo - Más de 2 horas'),
#     ], string='Color del Temporizador', compute='_compute_task_timer_color', store=False)
#
#     is_concluded = fields.Boolean(
#         string='Tarea Concluida',
#         compute='_compute_is_concluded',
#         store=True,
#         help='True si la tarea está en una fase de conclusión'
#     )
#
#     @api.depends('task_start_date', 'task_accumulated_time', 'timer_running')
#     def _compute_realtime_accumulated_time(self):
#         """Calcula el tiempo acumulado en tiempo real usando UTC"""
#         for task in self:
#             if task.timer_running and task.task_start_date:
#                 now_utc = fields.Datetime.now()
#                 elapsed = (now_utc - task.task_start_date).total_seconds()
#                 task.task_accumulated_time_realtime = int(task.task_accumulated_time + elapsed)
#             else:
#                 task.task_accumulated_time_realtime = task.task_accumulated_time
#
#     @api.depends('task_accumulated_time_realtime')
#     def _compute_task_timer(self):
#         """Campo técnico para el widget del temporizador"""
#         for task in self:
#             task.task_timer = str(task.task_accumulated_time_realtime)
#
#     @api.depends('task_accumulated_time_realtime')
#     def _compute_task_timer_color(self):
#         """Calcula el color del temporizador basado en el tiempo acumulado en tiempo real"""
#         ICP = self.env['ir.config_parameter'].sudo()
#         yellow_hours = float(ICP.get_param('rt_project_task_timer.yellow_hours', '1.0'))
#         red_hours = float(ICP.get_param('rt_project_task_timer.red_hours', '2.0'))
#
#         for task in self:
#             hours = task.task_accumulated_time_realtime / 3600.0  # Convertir segundos a horas
#
#             if hours >= red_hours:
#                 task.task_timer_color = 'red'
#             elif hours >= yellow_hours:
#                 task.task_timer_color = 'yellow'
#             else:
#                 task.task_timer_color = 'green'
#
#     @api.depends('stage_id', 'stage_id.fold')
#     def _compute_is_concluded(self):
#         """Determina si la tarea está en una fase de conclusión"""
#         for task in self:
#             task.is_concluded = task.stage_id and task.stage_id.fold
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         """Establece la fecha de inicio e inicia el temporizador al crear la tarea"""
#         for vals in vals_list:
#             if 'task_start_date' not in vals:
#                 vals['task_start_date'] = fields.Datetime.now()
#             if 'timer_running' not in vals:
#                 vals['timer_running'] = True
#         return super(ProjectTask, self).create(vals_list)
#
#     def write(self, vals):
#         """Detecta cuando una tarea se mueve a una fase de conclusión y detiene el temporizador"""
#         for task in self:
#             if task.timer_running and task.task_start_date and 'stage_id' in vals:
#                 now_utc = fields.Datetime.now()
#                 elapsed = (now_utc - task.task_start_date).total_seconds()
#                 total_time = int(task.task_accumulated_time + elapsed)
#
#                 vals['task_accumulated_time'] = total_time
#                 vals['task_start_date'] = now_utc
#
#         res = super(ProjectTask, self).write(vals)
#
#         if 'stage_id' in vals:
#             for task in self:
#                 if task.is_concluded:
#                     if task.timer_running:
#                         task.timer_running = False
#                     if not task.task_end_date:
#                         task.task_end_date = fields.Datetime.now()
#                 elif not task.is_concluded and task.task_end_date:
#                     task.timer_running = True
#                     task.task_start_date = fields.Datetime.now()
#                     task.task_end_date = False
#
#         return res
#
#     def get_task_timer_hours(self):
#         """Retorna el tiempo acumulado en horas (usado en vistas)"""
#         self.ensure_one()
#         return self.task_accumulated_time / 3600.0
