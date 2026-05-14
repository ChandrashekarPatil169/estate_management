from odoo import models, fields, api
from odoo.tools import format_date

class Project(models.Model):
    _inherit = "project.project"

    project_id = fields.Many2one('project.project', required=True)

    timeline_group_label = fields.Char(
        compute="_compute_timeline_group_label",
        store=True
    )

    @api.depends('name', 'user_id')
    def _compute_timeline_group_label(self):
        for rec in self:
            project = rec.name or "No Project"
            manager = rec.user_id.name if rec.user_id else "No Manager"
            rec.timeline_group_label = f"{project} - {manager}"


    # backlog_id = fields.One2many(
    #     'product.backlog',
    #     'project_id',
    #     string="Backlogs"
    # )
    #
    # epic_ids = fields.One2many(
    #     'project.epic',
    #     'project_id',
    #     string="Epics"
    # )
    #
    # user_story_ids = fields.One2many(
    #     'project.user.story',
    #     'project_id',
    #     string="Stories"
    # )
    #
    # task_ids = fields.One2many(
    #     'project.task',
    #     'project_id',
    #     string="Tasks"
    # )
    #
    # subtask_ids = fields.One2many(
    #     'project.subtask',
    #     'project_id',
    #     string="Subtasks"
    # )

#     # ---------------------------------------------------------
#     # HIERARCHY STRUCTURE
#     # ---------------------------------------------------------
#
#     hierarchy_display = fields.Text(
#         string="Hierarchy Display",
#         compute="_compute_hierarchy_display"
#     )
#
#     def _compute_hierarchy_display(self):
#         for project in self:
#             lines = []
#
#             def format_dates(rec):
#                 parts = []
#
#                 if getattr(rec, 'planned_start_date', False) and getattr(rec, 'planned_end_date', False):
#                     parts.append(
#                         f"Planned Date: {rec.planned_start_date} → {rec.planned_end_date}"
#                     )
#                 else:
#                     if getattr(rec, 'planned_start_date', False):
#                         parts.append(f"Planned Date: {rec.planned_start_date}")
#                     if getattr(rec, 'planned_end_date', False):
#                         parts.append(f"Planned Date: {rec.planned_end_date}")
#
#                 if getattr(rec, 'expected_end_date', False):
#                     parts.append(f"Exp: {rec.expected_end_date}")
#
#                 return " | ".join(parts)
#
#             # ---------------- TASK ----------------
#             for task in project.task_ids:
#                 task_dates = format_dates(task)
#                 lines.append(
#                     f"    ▸ {task.name}" +
#                     (f" | {task_dates}" if task_dates else "")
#                 )
#
#                 # ---------------- SUBTASK ----------------
#                 for sub in task.subtask_ids:
#                     sub_dates = format_dates(sub)
#                     lines.append(
#                         f"        ▸ {sub.name}" +
#                         (f" | {sub_dates}" if sub_dates else "")
#                     )
#
#             project.hierarchy_display = "\n".join(lines)
#
# # ---------------------------------------------------------
# # EXPECTED END DATE LOGIC
# # ---------------------------------------------------------
#
# @api.depends('planned_end', 'subtask_ids.expected_end_date')
# def _compute_expected_end_date(self):
#     """
#     Expected end date rule:
#     - If children exist → max child expected date
#     - Else → use own planned_end
#     """
#     for rec in self:
#         if rec.subtask_ids:
#             sub_dates = rec.subtask_ids.mapped('expected_end_date')
#             rec.expected_end_date = max(
#                 [d for d in sub_dates if d],
#                 default=rec.planned_end
#             )
#         else:
#             rec.expected_end_date = rec.planned_end
# #
# #
# # # ---------------------------------------------------------
# # # DISPLAY NAME (Optional: Clean Hierarchy Label)
# # # ---------------------------------------------------------
# #
# # def name_get(self):
# #     result = []
# #     for rec in self:
# #         level_map = dict(self._fields['level_type'].selection)
# #         prefix = level_map.get(rec.level_type, "")
# #         name = f"[{prefix}] {rec.name}" if prefix else rec.name
# #         result.append((rec.id, name))
# #     return result
