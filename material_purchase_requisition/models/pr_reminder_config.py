from odoo import models, fields
from dateutil.relativedelta import relativedelta

class PRApprovalReminderConfig(models.Model):
    _name = "pr.approval.reminder.config"

    _description = "PR Approval Reminder Configuration"

    delay_value = fields.Integer(
        string="Delay",
        required=True,
        default=3,
        tracking=True
    )
    delay_unit = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        string="Unit",
        required=True,
        default='days',
        tracking=True
    )
    active = fields.Boolean(default=True,tracking=True)

    def get_delay_delta(self):
        self.ensure_one()
        return relativedelta(**{self.delay_unit: self.delay_value})


























# from odoo import fields, models
# from odoo.exceptions import ValidationError
#
# class PRApprovalReminderConfig(models.Model):
#     _name = "pr.approval.reminder.config"
#     _description = "PR Approval Reminder Configuration"
#
#     delay_value = fields.Integer(required=True)
#     delay_unit = fields.Selection(
#         [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
#         required=True,
#     )
#     active = fields.Boolean(default=True)
