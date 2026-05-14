# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    task_timer_yellow_hours = fields.Float(
        string='Time for Yellow Color (hours)',
        default=1.0,
        config_parameter='rt_project_task_timer.yellow_hours',
        help='Time in hours after which the task will be displayed in yellow'
    )

    task_timer_red_hours = fields.Float(
        string='Time for Red Color (hours)',
        default=2.0,
        config_parameter='rt_project_task_timer.red_hours',
        help='Time in hours after which the task will be displayed in red'
    )

    @api.constrains('task_timer_yellow_hours', 'task_timer_red_hours')
    def _check_timer_hours(self):
        """Validate that red time is greater than yellow time"""
        for record in self:
            if record.task_timer_yellow_hours >= record.task_timer_red_hours:
                from odoo.exceptions import ValidationError
                raise ValidationError(
                    'The time for red color must be greater than the time for yellow color.'
                )
# # -*- coding: utf-8 -*-
# from odoo import models, fields, api
#
#
# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     task_timer_yellow_hours = fields.Float(
#         string='Tiempo para Color Amarillo (horas)',
#         default=1.0,
#         config_parameter='rt_project_task_timer.yellow_hours',
#         help='Tiempo en horas después del cual la tarea se mostrará en amarillo'
#     )
#
#     task_timer_red_hours = fields.Float(
#         string='Tiempo para Color Rojo (horas)',
#         default=2.0,
#         config_parameter='rt_project_task_timer.red_hours',
#         help='Tiempo en horas después del cual la tarea se mostrará en rojo'
#     )
#
#     @api.constrains('task_timer_yellow_hours', 'task_timer_red_hours')
#     def _check_timer_hours(self):
#         """Validar que el tiempo rojo sea mayor al tiempo amarillo"""
#         for record in self:
#             if record.task_timer_yellow_hours >= record.task_timer_red_hours:
#                 from odoo.exceptions import ValidationError
#                 raise ValidationError(
#                     'El tiempo para color rojo debe ser mayor al tiempo para color amarillo.'
#                 )
