from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TimesheetApproval(models.Model):
    _name = "timesheet.approval"
    _description = "Timesheet Approval"
    _order = "start_datetime desc"
    # _order = "date desc"

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        required=True,
    )

    parent_task_id = fields.Many2one(
        "project.task",
        string="Task",
        required=True,
        domain="[('project_id', '=', project_id), ('parent_id', '=', False)]"
    )

    subtask_id = fields.Many2one(
        "project.task",
        string="Subtask",
        required=True,
        domain="[('parent_id', '=', parent_task_id)]"
    )

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        default=lambda self: self.env.user.employee_id
    )

    start_datetime = fields.Datetime(
        string="Start Time",
        required=True,
        default=fields.Datetime.now
    )

    end_datetime = fields.Datetime(
        string="End Time",
        required=True
    )

    # date = fields.Date(
    #     required=True,
    #     default=fields.Date.today
    # )
    #
    # unit_amount = fields.Float(
    #     string="Time Spent",
    #     required=True
    # )

    description = fields.Char()



    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft')

    # Reset subtask when parent changes
    @api.onchange("parent_task_id")
    def _onchange_parent(self):
        self.subtask_id = False

    # Safety validation
    @api.constrains("parent_task_id", "subtask_id")
    def _check_subtask_parent(self):
        for rec in self:
            if rec.subtask_id.parent_id != rec.parent_task_id:
                raise ValidationError("Subtask must belong to selected Task.")

    @api.constrains('start_datetime', 'end_datetime')
    def _check_datetime_range(self):
        for rec in self:
            if rec.end_datetime <= rec.start_datetime:
                raise ValidationError("End Time must be after Start Time.")

    # Actions
    def action_submit(self):
        self.state = "submitted"

    def action_reject(self):
        self.state = "rejected"

    def action_reset_to_draft(self):
        self.state = "draft"

    def action_approve(self):
        for rec in self:
            duration = (rec.end_datetime - rec.start_datetime).total_seconds()
            hours = duration / 3600.0

            self.env["account.analytic.line"].create({
                "project_id": rec.project_id.id,
                "task_id": rec.subtask_id.id,
                "employee_id": rec.employee_id.id,
                "unit_amount": hours,
                "name": rec.description,
                "date": rec.start_datetime.date(),  # analytic still requires Date
            })

            rec.state = "approved"

    # def action_approve(self):
    #     for rec in self:
    #         # Create REAL timesheet only now
    #         self.env["account.analytic.line"].create({
    #             "project_id": rec.project_id.id,
    #             "task_id": rec.subtask_id.id,  # attach to subtask
    #             "employee_id": rec.employee_id.id,
    #             "unit_amount": rec.unit_amount,
    #             "name": rec.description,
    #             "date": rec.date,
    #         })
    #         rec.state = "approved"



# class AccountAnalyticLine(models.Model):
#     _inherit = "account.analytic.line"
#
#     # # 1️⃣ Parent Task (what user selects first)
#     # parent_task_id = fields.Many2one(
#     #     "project.task",
#     #     string="Task",
#     #     required=True,
#     # )
#     #
#     # # 2️⃣ Subtask (filtered by parent)
#     # subtask_id = fields.Many2one(
#     #     "project.task",
#     #     string="Subtask",
#     #     domain="[('parent_id', '=', parent_task_id)]",
#     #     required=True,
#     # )
#
#     # 3️⃣ Approval state
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#     ], default='draft')
#
#     # # 🔁 When subtask changes → set real task_id (technical field)
#     # @api.onchange("subtask_id")
#     # def _onchange_subtask(self):
#     #     if self.subtask_id:
#     #         self.task_id = self.subtask_id
#     #     else:
#     #         self.task_id = False
#
#     # 🔁 When parent changes → reset subtask
#     @api.onchange("parent_task_id")
#     def _onchange_parent(self):
#         self.subtask_id = False
#
#     # 🛑 Safety check
#     @api.constrains("task_id", "subtask_id")
#     def _check_subtask_parent(self):
#         for rec in self:
#             if rec.subtask_id and rec.subtask_id.parent_id != rec.task_id:
#                 raise ValidationError("Subtask must belong to selected Task.")
#     # @api.constrains("parent_task_id", "subtask_id")
#     # def _check_subtask_parent(self):
#     #     for rec in self:
#     #         if rec.subtask_id and rec.subtask_id.parent_id != rec.parent_task_id:
#     #             raise ValidationError("Subtask must belong to selected Task.")
#
#     # Approval actions
#     def action_submit(self):
#         self.state = 'submitted'
#
#     def action_approve(self):
#         self.state = 'approved'
#
#     def action_reject(self):
#         self.state = 'rejected'
#
#     def action_reset_to_draft(self):
#         self.state = 'draft'
# # from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
#
# class AccountAnalyticLine(models.Model):
#     _inherit = "account.analytic.line"
#
#     parent_task_id = fields.Many2one(
#         "project.task",
#         string="Task",
#         compute="_compute_parent_task",
#         store=True
#     )
#
#     subtask_id = fields.Many2one(
#         "project.task",
#         string="Subtask",
#         domain="[('parent_id','=',parent_task_id)]",
#         required=True
#     )
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('submitted', 'Submitted'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#     ], default='draft', tracking=True)
#
#     @api.onchange("subtask_id")
#     def _onchange_subtask(self):
#         if self.subtask_id:
#             self.task_id = self.subtask_id
#
#     @api.depends("subtask_id")
#     def _compute_parent_task(self):
#         for rec in self:
#             rec.parent_task_id = rec.subtask_id.parent_id if rec.subtask_id else False
#
#
# # from odoo import models , fields, api
# #
# #
# # class AccountAnalyticLine(models.Model):
# #     _inherit = "account.analytic.line"
# #
# #     parent_task_id = fields.Many2one(
# #         "project.task",
# #         string="Parent Task",
# #         compute="_compute_parent_task",
# #         store=True,
# #     )
# #
# #     subtask_id = fields.Many2one(
# #         "project.task",
# #         string="Subtask",
# #         domain="[('parent_id', '=', parent_task_id)]",
# #         required=True
# #     )
# #
# #     # subtask_id = fields.Many2one(
# #     #     "project.task",
# #     #     string="Subtask",
# #     #     domain="[('parent_id', '=', task_id)]"
# #     # )
# #
# #     state = fields.Selection([
# #         ('draft', 'Draft'),
# #         ('submitted', 'Submitted'),
# #         ('approved', 'Approved'),
# #         ('rejected', 'Rejected'),
# #     ], default='draft', tracking=True)
# #
# #     def action_approve(self):
# #         for rec in self:
# #             rec.state = 'approved'
# #
# #             # Ensure task_id is subtask if selected
# #             if rec.subtask_id:
# #                 rec.task_id = rec.subtask_id.id
# #
# #     def action_reject(self):
# #         self.state = 'rejected'
# #
# #     def action_reset_to_draft(self):
# #         self.state = 'draft'
# #
# #     def action_submit(self):
# #         for rec in self:
# #             rec.state = 'submitted'
# #
# #     @api.onchange('task_id')
# #     def _onchange_task_id(self):
# #         self.subtask_id = False
# #
# #     @api.onchange("subtask_id")
# #     def _onchange_subtask(self):
# #         if self.subtask_id:
# #             self.task_id = self.subtask_id
# #
# #     @api.depends("task_id", "task_id.parent_id")
# #     def _compute_parent_task(self):
# #         for rec in self:
# #             rec.parent_task_id = rec.task_id.parent_id if rec.task_id else False
# #
# #     @api.model_create_multi
# #     def create(self, vals_list):
# #         for vals in vals_list:
# #             if vals.get("subtask_id"):
# #                 vals["task_id"] = vals["subtask_id"]
# #         return super().create(vals_list)
# #
# #     @api.constrains("parent_task_id", "subtask_id")
# #     def _check_subtask_parent(self):
# #         for rec in self:
# #             if rec.subtask_id.parent_id != rec.parent_task_id:
# #                 raise ValidationError("Subtask must belong to selected Task.")
# #
# #     # def read_group(
# #     #     self,
# #     #     domain,
# #     #     fields,
# #     #     groupby,
# #     #     offset=0,
# #     #     limit=None,
# #     #     orderby=False,
# #     #     lazy=True,
# #     # ):
# #     #     result = super().read_group(
# #     #         domain, fields, groupby,
# #     #         offset=offset,
# #     #         limit=limit,
# #     #         orderby=orderby,
# #     #         lazy=lazy,
# #     #     )
# #     #
# #     #     # Remove groups where grouped field is False
# #     #     cleaned_result = []
# #     #
# #     #     for group in result:
# #     #         remove = False
# #     #
# #     #         for gb in groupby:
# #     #             field_name = gb.split(":")[0]
# #     #
# #     #             if field_name in group and not group[field_name]:
# #     #                 remove = True
# #     #                 break
# #     #
# #     #         if not remove:
# #     #             cleaned_result.append(group)
# #     #
# #     #     return cleaned_result
# #
