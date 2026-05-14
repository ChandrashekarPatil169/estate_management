from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import string
from datetime import date

class ProjectProject(models.Model):
    _inherit = "project.project"

    # 🔴 HIERARCHY CONFIGURATION
    _parent_name = "parent_project_id"
    _parent_store = True

    parent_path = fields.Char(index=True)

    # ----------------------------
    # Reference fields
    # ----------------------------
    ref_code = fields.Char(
        string="Project Ref",
        readonly=True,
        copy=False,
        index=True
    )

    ref_sequence = fields.Integer(
        string="Ref Sequence",
        readonly=True,
        copy=False
    )

    _sql_constraints = [
        ('project_ref_unique', 'unique(ref_code)', 'Project reference must be unique!')
    ]

    parent_project_id = fields.Many2one(
        "project.project",
        string="Parent Project",
        ondelete="restrict",
        index=True
    )

    sub_project_ids = fields.One2many(
        "project.project",
        "parent_project_id",
        string="Sub-Projects"
    )

    sub_project_count = fields.Integer(
        compute="_compute_sub_project_count"
    )

    is_current_user_approver = fields.Boolean(
        compute='_compute_is_current_user_approver',
        store=False
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='draft', string="Status")

    reject_reason = fields.Text(
        string="Reject Reason",
        readonly=True
    )



    # Prevent parent change after save
    def write(self, vals):
        for rec in self:
            if (
                    rec.parent_project_id
                    and "parent_project_id" in vals
                    and vals["parent_project_id"] != rec.parent_project_id.id
            ):
                raise ValidationError(
                    _("Parent Project cannot be changed once set.")
                )
        return super().write(vals)

    @api.depends("sub_project_ids")
    def _compute_sub_project_count(self):
        for rec in self:
            rec.sub_project_count = len(rec.sub_project_ids)

    def unlink(self):
        for rec in self:
            if rec.sub_project_ids:
                raise ValidationError(
                    _("Cannot delete project with sub-projects.")
                )
        return super().unlink()

    # @api.depends("sub_project_ids")
    # def _compute_sub_project_count(self):
    #     for rec in self:
    #         rec.sub_project_count = len(rec.sub_project_ids)

    # def action_open_sub_projects(self):
    #     self.ensure_one()
    #
    #     action_id = self.env.context.get('params', {}).get('action')
    #     if action_id:
    #         action = self.env['ir.actions.act_window'].browse(action_id).read()[0]
    #     else:
    #         action = {
    #             'type': 'ir.actions.act_window',
    #             'res_model': 'project.project',
    #             'view_mode': 'kanban,list,form',
    #         }
    #
    #     action.update({
    #         'name': _('Sub-Projects'),
    #         'domain': [('parent_project_id', '=', self.id)],
    #         'context': {
    #             'default_parent_project_id': self.id,
    #             'search_default_parent_project_id': self.id,
    #             # 'group_by': ['stage_id'],  # 🔑 THIS shows stages
    #         },
    #     })
    def action_open_sub_projects(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub-Projects',
            'res_model': 'project.project',
            'view_mode': 'kanban,list,form',
            'domain': [('parent_project_id', '=', self.id)],
            'context': {
                'default_parent_project_id': self.id,
                'search_default_parent_project_id': self.id,
                'group_by': False,  # 🔥 IMPORTANT
            },
        }



    # def action_open_sub_projects(self):
    #     self.ensure_one()
    #     return {
    #         "type": "ir.actions.act_window",
    #         "name": _("Sub-Projects"),
    #         "res_model": "project.project",
    #         "view_mode": "kanban,list,form",
    #         "domain": [("parent_project_id", "=", self.id)],
    #         "context": {"default_parent_project_id": self.id},
    #     }
    @api.constrains("parent_project_id")
    def _check_no_circular_parent(self):
        for rec in self:
            parent = rec.parent_project_id
            while parent:
                if parent == rec:
                    raise ValidationError(_("Circular project hierarchy detected."))
                parent = parent.parent_project_id

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)

        # CHANGE 1: timezone-safe year (bug fix)
        current_year = fields.Date.context_today(self).year
        year_prefix = f"{current_year}/PR"

        for project in projects:
            if project.ref_code:
                continue

            parent = project.parent_project_id

            # -------------------------
            # ROOT PROJECT → 2026/PR1
            # -------------------------
            if not parent:
                last = self.search(
                    [
                        ('parent_project_id', '=', False),
                        ('ref_sequence', '!=', False),  # CHANGE 2: avoid broken records
                        ('ref_code', 'like', f'{year_prefix}%')
                    ],
                    order="ref_sequence desc",
                    limit=1
                )

                next_seq = (last.ref_sequence or 0) + 1
                ref_code = f"{year_prefix}{next_seq}"

                project.ref_sequence = next_seq
                project.ref_code = ref_code

            # -------------------------
            # SUB PROJECT
            # -------------------------
            else:
                # CHANGE 3: defensive guard (fixes your RPC crash)
                parent_ref = parent.ref_code
                if not parent_ref or not isinstance(parent_ref, str):
                    raise ValidationError(
                        "Parent project must have a valid Reference Code before creating sub-projects."
                    )

                siblings = self.search(
                    [
                        ('parent_project_id', '=', parent.id),
                        ('ref_sequence', '!=', False),  # CHANGE 4: sequence safety
                    ],
                    order="ref_sequence desc",
                    limit=1
                )

                next_seq = (siblings.ref_sequence or 0) + 1
                project.ref_sequence = next_seq

                # Parent ends with digit → alphabet suffix
                if parent_ref[-1].isdigit():  # CHANGE 5: safe usage
                    # CHANGE 6: prevent IndexError after Z
                    if next_seq <= 26:
                        suffix = string.ascii_uppercase[next_seq - 1]
                    else:
                        raise ValidationError(
                            "Maximum sub-project limit exceeded (A–Z)."
                        )
                    ref_code = f"{parent_ref}{suffix}"
                else:
                    # Parent ends with letter → numeric suffix
                    ref_code = f"{parent_ref}{next_seq}"

                project.ref_code = ref_code

            # -------------------------
            # 🔑 MUTATE NAME (ONCE)
            # -------------------------
            if project.name and not project.name.startswith(project.ref_code):
                project.name = f"{project.ref_code} - {project.name}"

        return projects

    # @api.model_create_multi
    # def create(self, vals_list):
    #     projects = super().create(vals_list)
    #
    #     current_year = date.today().year
    #     year_prefix = f"{current_year}/PR"
    #
    #     for project in projects:
    #         if project.ref_code:
    #             continue
    #
    #         parent = project.parent_project_id
    #
    #         # -------------------------
    #         # ROOT PROJECT → 2026/PR1
    #         # -------------------------
    #         if not parent:
    #             last = self.search(
    #                 [
    #                     ('parent_project_id', '=', False),
    #                     ('ref_code', 'like', f'{year_prefix}%')
    #                 ],
    #                 order="ref_sequence desc",
    #                 limit=1
    #             )
    #
    #             next_seq = (last.ref_sequence or 0) + 1
    #             ref_code = f"{year_prefix}{next_seq}"
    #
    #             project.ref_sequence = next_seq
    #             project.ref_code = ref_code
    #
    #         # -------------------------
    #         # SUB PROJECT
    #         # -------------------------
    #         else:
    #             siblings = self.search(
    #                 [('parent_project_id', '=', parent.id)],
    #                 order="ref_sequence desc",
    #                 limit=1
    #             )
    #
    #             next_seq = (siblings.ref_sequence or 0) + 1
    #             project.ref_sequence = next_seq
    #
    #             # Parent ends with digit → alphabet suffix
    #             if parent.ref_code[-1].isdigit():
    #                 suffix = string.ascii_uppercase[next_seq - 1]
    #                 ref_code = f"{parent.ref_code}{suffix}"
    #             else:
    #                 # Parent ends with letter → numeric suffix
    #                 ref_code = f"{parent.ref_code}{next_seq}"
    #
    #             project.ref_code = ref_code
    #
    #         # -------------------------
    #         # 🔑 MUTATE NAME (ONCE)
    #         # -------------------------
    #         if project.name and not project.name.startswith(project.ref_code):
    #             project.name = f"{project.ref_code} - {project.name}"
    #
    #     return projects

    def name_get(self):
        result = []
        for rec in self:
            if rec.ref_code and rec.name:
                display_name = f"{rec.ref_code} - {rec.name}"
            else:
                display_name = rec.name or ''
            result.append((rec.id, display_name))
        return result

    def _name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|', ('ref_code', operator, name), ('name', operator, name)] + args
        return super()._name_search(name='', args=args, operator=operator, limit=limit)

