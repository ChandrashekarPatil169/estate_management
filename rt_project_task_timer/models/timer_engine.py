from odoo import models, fields
from odoo.exceptions import UserError


class TimerEngine(models.AbstractModel):
    _name = 'timer.engine'
    _description = 'Reusable Timer Engine'

    timer_start = fields.Datetime(copy=False)
    timer_running = fields.Boolean(default=False, copy=False)

    def action_start_timer(self):
        for rec in self:
            if not rec.timer_running:
                rec.timer_start = fields.Datetime.now()
                rec.timer_running = True

    def action_stop_timer(self):
        for rec in self:
            if not rec.timer_running or not rec.timer_start:
                continue

            now = fields.Datetime.now()
            seconds = int((now - rec.timer_start).total_seconds())
            hours = seconds / 3600.0

            employee = self.env.user.employee_id
            if not employee:
                raise UserError("User not linked to employee.")

            rec._create_timesheet_line(hours)

            rec.timer_running = False
            rec.timer_start = False