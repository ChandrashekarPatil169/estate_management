from datetime import date, timedelta
from odoo.exceptions import ValidationError, UserError,AccessError
from odoo import models, fields, api,_
import logging


_logger = logging.getLogger(__name__)


class ProjectUserStory(models.Model):
    _name = 'project.user.story'
    _description = 'User Story'
    _inherit = ['scheduler.mixin', 'mail.thread', 'mail.activity.mixin', 'hierarchy.sequence.mixin']

    name = fields.Char(string="Story Title", required=True, tracking=True)
    project_id = fields.Many2one('project.project', required=True)
    epic_id = fields.Many2one('project.epic')
    ################################
    code = fields.Char(readonly=True)
    sequence_no = fields.Integer(readonly=True)
    #################################
    enable_backlog_flow = fields.Boolean(
        related='project_id.enable_backlog_flow',
        store=False,
        readonly=True
    )

    persona = fields.Char()
    business_value = fields.Integer(string="Business Value (1-5)")

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])

    story_points = fields.Integer()
    ready = fields.Boolean(string="Do You Need (DoR)")

    status = fields.Selection([
        ('new', 'New'),
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold'),
        ('review', 'Review'),
        ('done', 'Complete'),
        ('cancelled', 'Cancelled'),
    ], default='new', tracking=True)

    # 🔥 Kanban Status (for colored dot widget)
    kanban_state = fields.Selection([
        ('new', 'New'),
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold'),
        ('review', 'Review'),
        ('done', 'Complete'),
        ('cancelled', 'Cancelled'),
    ], default='new', tracking=True)
    estimated = fields.Float(string="Estimate")
    sla_due_date = fields.Date()
    sla_status = fields.Selection([
        ('green', 'Green'),
        ('amber', 'Amber'),
        ('red', 'Red'),
    ], compute='_compute_sla_status', store=True)

    days_remaining = fields.Integer(compute='_compute_sla_status', store=True)

    connextra_story = fields.Text(string="Connextra Story")
    given = fields.Text()
    when = fields.Text()
    then = fields.Text()
    dod_checklist = fields.Text()

    acceptance_required = fields.Boolean()
    acceptance_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])

    subtask_ids = fields.One2many('project.subtask', 'story_id')
    # ✅ THE ONLY task relation you need
    task_ids = fields.One2many(
        'project.task',
        'story_id',
        string="Tasks"
    )

    task_count = fields.Integer(compute='_compute_task_count', string="Task Count")

    # Document Management Logic
    document_ids = fields.Many2many('ir.attachment', compute='_compute_document_ids', inverse='_inverse_document_ids')
    document_count = fields.Integer(compute='_compute_document_count')
    expected_end_date = fields.Date(string="Expected End Date", readonly=True)

    approver_ids = fields.Many2many(
        'res.users',
        string="Approvers",
        tracking=True
    )

    approved_by_id = fields.Many2one(
        'res.users',
        string="Approved By",
        readonly=True,
        tracking=True
    )

    is_done = fields.Boolean(
        string="Done",
        readonly=True,
        tracking=True
    )

    evidence_required = fields.Html(
        string="Evidence Required"
    )
    all_tasks_done = fields.Boolean(
        string="All Tasks Done",
        compute="_compute_all_tasks_done",
        store=True,
    )

    description = fields.Html("User Story Notes")

    inherited_notes = fields.Html(
        compute="_compute_inherited_notes",
        sanitize=False
    )

    assignee_id = fields.Many2one(
        'res.users',
        required=False,
        tracking=True
    )

    ###############################

    # SLA Risk (derived)
    sla_risk = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_task_sla",
        store=True,
    )

    sla_escalation_rules = fields.Text(string="SLA Escalation Rules")

    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'story_sla_amber_rel',
        'story_id',
        'user_id',
        string="Amber Escalation Owners"
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'story_sla_red_rel',
        'story_id',
        'user_id',
        string="Red Escalation Owners"
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'story_sla_overdue3_rel',
        'story_id',
        'user_id',
        string="Overdue +3 Days Owners"
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'story_sla_overdue6_rel',
        'story_id',
        'user_id',
        string="Overdue +6 Days Owners"
    )

    sla_state = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_task_sla",
        store=True,
    )

    sla_days_remaining = fields.Integer(
        compute="_compute_task_sla",
        store=True,
    )

    sla_stage = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red'),
            ('red_3', 'Overdue +3 Days'),
            ('red_6', 'Overdue +6 Days'),
        ],
        compute="_compute_task_sla",
        store=True,
    )

    planned_start_date = fields.Date(string="Planned Start Date")
    planned_end_date = fields.Date(string="Planned End Date")
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
        copy=False
    )

    sla_days_label = fields.Char(
        string="SLA Days",
        compute="_compute_sla_days_label",
        store=True,
    )

    @api.depends('sla_days_remaining', 'is_done')
    def _compute_sla_days_label(self):
        for task in self:
            days = task.sla_days_remaining

            if task.is_done:
                task.sla_days_label = "Completed"
            elif days > 0:
                task.sla_days_label = f"{days} days remaining"
            elif days == 0:
                task.sla_days_label = "Due today"
            else:
                task.sla_days_label = f"{abs(days)} days overdue"

    def _get_parent_field(self):
        return 'epic_id'

    @api.depends(
        'planned_end_date',
        'status',
        'is_done',
        'task_ids.status',
        'task_ids.planned_end_date'
    )
    def _compute_task_sla(self):
        today = fields.Date.today()

        for story in self:
            if story.is_done or not story.planned_end_date:
                story.sla_risk = 'green'
                story.sla_state = 'green'
                story.sla_stage = 'green'
                story.sla_days_remaining = 0
                continue

            delta_days = (story.planned_end_date - today).days
            story.sla_days_remaining = delta_days

            if delta_days > 3:
                story.sla_risk = 'green'
                story.sla_state = 'green'
                story.sla_stage = 'green'
            elif 0 < delta_days <= 3:
                story.sla_risk = 'amber'
                story.sla_state = 'amber'
                story.sla_stage = 'amber'
            elif 0 >= delta_days > -3:
                story.sla_risk = 'red'
                story.sla_state = 'red'
                story.sla_stage = 'red'
            elif -3 >= delta_days > -6:
                story.sla_risk = 'red'
                story.sla_state = 'red'
                story.sla_stage = 'red_3'
            else:
                story.sla_risk = 'red'
                story.sla_state = 'red'
                story.sla_stage = 'red_6'

    def action_open_task_sla_7_days(self):
        self.ensure_one()
        today = fields.Date.today()
        limit_date = today + timedelta(days=7)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Tasks - Next 7 Days',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [
                ('story_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
        }

    def action_open_task_sla_30_days(self):
        self.ensure_one()
        today = fields.Date.today()
        limit_date = today + timedelta(days=30)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Tasks - Next 30 Days',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [
                ('story_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
        }

    # def action_open_subtask_sla_30_days(self):
    #     self.ensure_one()
    #
    #     today = fields.Date.today()
    #     limit_date = today + timedelta(days=30)
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Upcoming Subtasks - Next 30 Days',
    #         'res_model': 'project.task',  # 🔥 MUST BE THIS
    #         'view_mode': 'list,form',
    #         'domain': [
    #             ('story_id', '=', self.id),
    #             ('planned_end_date', '>=', today),
    #             ('planned_end_date', '<=', limit_date),
    #             ('status', '!=', 'done'),
    #         ],
    #     }

    # def _compute_subtask_sla(self):
    #     today = fields.Date.today()
    #
    #     for task in self:
    #
    #         open_subtasks = task.subtask_ids.filtered(
    #             lambda s: s.status != 'done' and s.planned_end_date
    #         )
    #
    #         if not open_subtasks:
    #             task.sla_risk = 'green'
    #             continue
    #
    #         # Strict governance → earliest deadline controls risk
    #         earliest_deadline = min(open_subtasks.mapped('planned_end_date'))
    #         delta_days = (earliest_deadline - today).days
    #
    #         if delta_days > 3:
    #             task.sla_risk = 'green'
    #
    #         elif 0 < delta_days <= 3:
    #             task.sla_risk = 'amber'
    #
    #         else:
    #             task.sla_risk = 'red'

    # def action_open_sla_monitoring(self):
    #     self.ensure_one()
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'SLA Monitoring',
    #         'res_model': 'project.task',
    #         'view_mode': 'kanban,list,form',
    #         'domain': [
    #             ('story_id', '=', self.id),
    #             ('status', '!=', 'done'),
    #         ],
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #     }

    # def action_open_sla_monitoring(self):
    #     self.ensure_one()
    #
    #     kanban_view = self.env.ref(
    #         'project_main_mgmt.view_task_sla_kanban'
    #     )
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'SLA Monitoring',
    #         'res_model': 'project.task',
    #         'view_mode': 'kanban,list,form',
    #         'views': [
    #             (kanban_view.id, 'kanban'),
    #             (False, 'list'),
    #             (False, 'form'),
    #         ],
    #         'domain': [
    #             ('story_id', '=', self.id),
    #             ('status', '!=', 'done'),
    #         ],
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #     }
    def action_open_sla_monitoring(self):
        self.ensure_one()

        kanban_view = self.env.ref(
            'project_main_mgmt.view_task_sla_kanban'
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': 'project.task',
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view.id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': [
                ('story_id', '=', self.id),
                # ('status', '!=', 'done'),
            ],
            'context': {
                'group_by': ['sla_stage'],
            },
        }

    #########################

    def _get_project_identifier(self, project):
        """
        Extracts '2026/PR8' from:
        '2026/PR8 - ASURE'
        """
        if not project.name:
            raise ValidationError(
                "Project name is empty. Cannot derive project identifier."
            )

        if ' - ' not in project.name:
            raise ValidationError(
                "Invalid Project Name format.\n"
                "Expected: YEAR/PROJECT_CODE - Description\n"
                "Example: 2026/PR8 - ASURE"
            )

        # ✅ STRICT: take only what comes before ' - '
        return project.name.split(' - ', 1)[0].strip()

    @api.model_create_multi
    def create(self, vals_list):

        if not self.env.user.has_group('base.group_system'):
            for vals in vals_list:
                if vals.get('planned_start_date') or vals.get('planned_end_date'):
                    project = False

                    if vals.get('project_id'):
                        project = self.env['project.project'].browse(vals['project_id'])
                    elif vals.get('epic_id'):
                        epic = self.env['project.epic'].browse(vals['epic_id'])
                        project = epic.project_id

                    if project and not project._current_user_has_deadline_change_access():
                        raise AccessError(_("You do not have Changing Deadline access for this project."))

        for vals in vals_list:
            epic_id = vals.get('epic_id') or self.env.context.get('default_epic_id')
            project_id = vals.get('project_id') or self.env.context.get('default_project_id')

            epic = False
            if epic_id:
                epic = self.env['project.epic'].browse(epic_id)
                project_id = project_id or epic.project_id.id

            if not project_id and epic:
                project_id = epic.project_id.id

            if not project_id:
                raise ValidationError(_("User Story must be created from Project or Epic."))

            project = self.env['project.project'].browse(project_id)

            if project.enable_backlog_flow:
                if not epic_id:
                    raise ValidationError(_(
                        "User Story must be created only from Epic when 'Enable Backlog & Epic' is ON.\n\n"
                        "Valid flow:\n"
                        "Project → Product Backlog → Epic → User Story → Task → Subtask"
                    ))
            else:
                if epic_id:
                    raise ValidationError(_(
                        "User Story must be created directly from Project when 'Enable Backlog & Epic' is OFF.\n\n"
                        "Valid flow:\n"
                        "Project → User Story → Task → Subtask"
                    ))




        records = super().create(vals_list)

        for rec in records:
            project = rec.project_id
            enable_flow = getattr(project, 'enable_backlog_flow', True)

            # 🔹 Epic-based flow
            if enable_flow and rec.epic_id and rec.epic_id.code:
                seq = rec._next_sequence([
                    ('epic_id', '=', rec.epic_id.id),
                ])
                rec.sequence_no = seq
                rec.code = f"{rec.epic_id.code}-US{seq}"

            # 🔹 Project-based flow (FULL project identifier)
            else:
                seq = rec._next_sequence([
                    ('project_id', '=', project.id),
                ])
                rec.sequence_no = seq

                project_identifier = rec._get_project_identifier(project)
                rec.code = f"{project_identifier}-US{seq}"

            # ✅ Prefix name once
            if rec.name and not rec.name.startswith(rec.code):
                rec.name = f"{rec.code} - {rec.name}"

        return records

    def _check_project_follower_kanban_drag_access(self):

        for rec in self:
            if rec._is_full_project_manager_access():
                continue
            project = rec.project_id or (rec.epic_id.project_id if rec.epic_id else False)
            if project and not project._current_user_has_kanban_drag_access():
                raise AccessError(_("You do not have Kanban Drag & Drop access for this project."))

    def _check_project_follower_governance_access(self):

        for rec in self:
            if rec._is_full_project_manager_access():
                continue
            project = rec.project_id or (rec.epic_id.project_id if rec.epic_id else False)
            if project and not project._current_user_has_governance_access():
                raise AccessError(_("You do not have Governance access for this project."))

    def _check_project_follower_deadline_access(self):

        for rec in self:
            # Admin / Program Manager / Project Manager -> full access
            if rec._is_full_project_manager_access():
                continue
            project = rec.project_id or (rec.epic_id.project_id if rec.epic_id else False)
            if project and not project._current_user_has_deadline_change_access():
                raise AccessError(_("You do not have Changing Deadline access for this project."))

    def _is_full_project_manager_access(self):
        self.ensure_one()

        project = self.project_id or (self.epic_id.project_id if self.epic_id else False)

        if not project:
            return self.env.user.has_group('base.group_system')

        return project._is_full_project_manager_access()

    def write(self, vals):

        if self.env.context.get('skip_scheduler_chain'):
            return super(ProjectUserStory, self).write(vals)

        self._check_story_readonly_access(vals)
        # 🔹 Sync colored dot with status
        if 'status' in vals:
            vals['kanban_state'] = vals['status']

        # 🔥 Kanban drag/drop access
        if (
                not self.env.context.get('skip_story_kanban_check')
                and any(k in vals for k in [
            'stage_id',
            'status',
            'kanban_state',
            'state',
            'sequence',
            'date_last_stage_update'
        ])
        ):
            for rec in self:
                # allow approver only through approval button flow
                if (
                        self.env.context.get('from_story_approval')
                        and rec._is_current_user_story_approver()
                        and set(vals.keys()).issubset({
                    'status', 'kanban_state', 'approved_by_id', 'completed_date', 'is_done'
                })
                ):
                    continue
                rec._check_project_follower_kanban_drag_access()

            # ✅ Governance access
        if (
                not self.env.context.get('skip_story_governance_check')
                and any(k in vals for k in [
            'approver_ids',
            'approved_by_id',
            'is_done',
            'evidence_required'
        ])
        ):
            for rec in self:
                # Admin / Program Manager / Project Manager
                if rec._is_full_project_manager_access():
                    continue

                # Allow assigned approver only for approval button flow
                if (
                        self.env.context.get('from_story_approval')
                        and rec._is_current_user_story_approver()
                        and set(vals.keys()).issubset({
                    'status', 'kanban_state', 'approved_by_id', 'completed_date', 'is_done'
                })
                ):
                    continue

                if not rec._current_user_has_governance_access():
                    raise AccessError(_("You do not have Governance access for this user story."))

        # 🔥 Deadline access
        is_kanban_drag = any(k in vals for k in [
            'stage_id',
            'status',
            'kanban_state',
            'state',
            'sequence',
            'date_last_stage_update'
        ])
        if 'planned_start_date' in vals or 'planned_end_date' in vals:
            if not (
                    self.env.context.get('from_kanban_drag_auto')
                    or self.env.context.get('skip_scheduler_chain')
                    or self.env.context.get('skip_deadline_access_check')
                    or (
                            is_kanban_drag and all(
                        (rec.project_id or (rec.epic_id.project_id if rec.epic_id else False))
                        and (rec.project_id or rec.epic_id.project_id)._current_user_has_kanban_drag_access()
                        for rec in self
                    )
                    )
            ):
                self._check_project_follower_deadline_access()

        return super(ProjectUserStory, self).write(vals)

    def _is_project_user_readonly_mode(self):
        for rec in self:
            if rec._is_full_project_manager_access():
                return False
        return self.env.user.has_group('project.group_project_user')

    def _check_story_readonly_access(self, vals):

        if self.env.context.get('skip_story_readonly_check'):
            return

        if not self._is_project_user_readonly_mode():
            return
        # for rec in self:
        #     if rec._is_full_project_manager_access():
        #         return

        allowed_fields = {
            # Chatter / Activities
            'message_follower_ids',
            'message_partner_ids',
            'message_ids',
            'message_main_attachment_id',

            # Deadline fields
            'planned_start_date',
            'planned_end_date',
            'expected_end_date',
            'completed_date',

            # Governance fields
            'approver_ids',
            'approved_by_id',
            'is_done',
            'evidence_required',

            # Kanban / Stage fields
            'stage_id',
            'status',
            'state',
            'kanban_state',
            'sequence',
            'date_last_stage_update',
        }

        technical_ok = {
            'write_date',
            'write_uid',
            '__last_update',
        }

        forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
        if forbidden:
            raise AccessError(_("User Story is read-only. You can only use Chatter."))

    # @api.depends(
    #     'epic_id.description',
    #     'epic_id.backlog_id.description',
    #     'epic_id.backlog_id.project_id.description'
    # )
    # def _compute_inherited_notes(self):
    #     for rec in self:
    #         project_note = rec.epic_id.backlog_id.project_id.description or ""
    #
    #         backlog_note = rec.epic_id.backlog_id.description or ""
    #         epic_note = rec.epic_id.description or ""
    #
    #         rec.inherited_notes = f"""
    #         <h4>Project Notes</h4>{project_note}
    #         <hr/>
    #         <h4>Backlog Notes</h4>{backlog_note}
    #         <hr/>
    #         <h4>Epic Notes</h4>{epic_note}
    #         """
    @api.depends(
        'project_id.description',
        'epic_id.description',
        'epic_id.backlog_id.description',
        'epic_id.backlog_id.project_id.description',
        'project_id.enable_backlog_flow',
        'epic_id.backlog_id.project_id.enable_backlog_flow'
    )
    def _compute_inherited_notes(self):
        for rec in self:
            project = rec.project_id or (
                rec.epic_id.backlog_id.project_id if rec.epic_id and rec.epic_id.backlog_id else False)

            project_note = project.description or "" if project else ""
            backlog_note = rec.epic_id.backlog_id.description or "" if rec.epic_id and rec.epic_id.backlog_id else ""
            epic_note = rec.epic_id.description or "" if rec.epic_id else ""

            sections = []

            # Always show Project Notes
            if project_note:
                sections.append(f"<h4>Project Notes</h4>{project_note}")

            # Show Backlog + Epic only when toggle ON
            if project and project.enable_backlog_flow:
                if backlog_note:
                    sections.append(f"<hr/><h4>Backlog Notes</h4>{backlog_note}")
                if epic_note:
                    sections.append(f"<hr/><h4>Epic Notes</h4>{epic_note}")

            rec.inherited_notes = "".join(sections)


    # @api.depends('task_ids.state')
    # def _compute_all_tasks_done(self):
    #     for story in self:
    #         if not story.task_ids:
    #             story.all_tasks_done = False
    #         else:
    #             story.all_tasks_done = all(
    #                 task.state == '1_done'
    #                 for task in story.task_ids
    #             )
    @api.depends('task_ids.status')
    def _compute_all_tasks_done(self):
        for story in self:
            if not story.task_ids:
                story.all_tasks_done = False

        else:
            story.all_tasks_done = all(
                task.status == 'done' for task in story.task_ids
            )

    # def action_governance_approve(self):
    #     self.ensure_one()
    #
    #     # Already approved
    #     if self.status == 'done':
    #         return
    #
    #     # 🚨 HARD GOVERNANCE CHECK
    #     if not self.all_tasks_done:
    #         raise ValidationError(
    #             "Governance approval is not allowed until ALL tasks are Done."
    #         )
    #
    #     self.write({
    #         'status': 'done',
    #         'kanban_state': 'done',
    #         'approved_by_id': self.env.user.id,
    #     })

    def _is_current_user_story_approver(self):
        self.ensure_one()
        return self.env.user in self.approver_ids

    def action_governance_approve(self):
        self.ensure_one()

        if self.status == 'done':
            return

        pending = self.task_ids.filtered(lambda t: t.status != 'done')

        if pending:
            raise ValidationError(
                "Governance approval is not allowed until ALL tasks are Done."
            )

        self.with_context(
            skip_story_readonly_check=True,
            skip_story_kanban_check=True,
            skip_story_governance_check=True,
            skip_deadline_access_check=True,
            from_story_approval=True,
        ).write({
            'status': 'done',
            'kanban_state': 'done',
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
            'is_done': True,
        })

    def _compute_document_ids(self):
        for record in self:
            record.document_ids = self.env['ir.attachment'].search([
                ('res_model', '=', self._name), ('res_id', '=', record.id)
            ])

    def _inverse_document_ids(self):
        for record in self:
            for attachment in record.document_ids:
                if not attachment.res_model:
                    attachment.write({'res_model': self._name, 'res_id': record.id})

    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name), ('res_id', '=', record.id)
            ])

    def action_view_story_documents(self):
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',  # 'list' is required for Odoo 17+
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    @api.depends('task_ids')
    def _compute_task_count(self):
        for rec in self:
            rec.task_count = len(rec.task_ids)

    def action_view_story_tasks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'list,kanban,form,timeline',
            'domain': [('story_id', '=', self.id)],
            'context': {
                'default_story_id': self.id,
                'default_project_id': self.project_id.id,
                'story_governed_create': True
            },
        }

    @api.depends('sla_due_date')
    def _compute_sla_status(self):
        today = date.today()
        for rec in self:
            if rec.sla_due_date:
                delta = (rec.sla_due_date - today).days
                rec.days_remaining = delta
                if delta > 3:
                    rec.sla_status = 'green'
                elif 0 <= delta <= 3:
                    rec.sla_status = 'amber'
                else:
                    rec.sla_status = 'red'
            else:
                rec.sla_status = False
                rec.days_remaining = 0

    @api.onchange('story_id')
    def _onchange_story_id(self):
        if self.story_id:
            self.project_id = self.story_id.project_id

    task_avg_progress = fields.Float(
        string="Task Avg %",
        compute="_compute_task_avg_progress",
        store=True
    )

    progress_color = fields.Char(
        string="Progress Color",
        compute="_compute_progress_color",
        store=False
    )

    @api.depends("task_avg_progress")
    def _compute_progress_color(self):
        # get first config (assuming single master config)
        config = self.env['progress.config'].search([], limit=1)

        lines = config.line_ids.sorted(key=lambda l: l.min_value) if config else []

        for rec in self:
            color = 'bg-primary'  # fallback

            for line in lines:
                if line.min_value <= rec.task_avg_progress <= line.max_value:
                    color = line.color
                    break

            rec.progress_color = color

    @api.depends('task_ids.task_progress')
    def _compute_task_avg_progress(self):
        for story in self:
            if story.task_ids:
                vals = story.task_ids.mapped('task_progress')
                story.task_avg_progress = sum(vals) / len(vals)
            else:
                story.task_avg_progress = 0
####################################################################
    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    # ✅ FIXED NAME
    @api.model
    def _cron_recompute_story_sla(self):
        stories = self.search([
            ('planned_end_date', '!=', False),
            ('is_done', '=', False),
        ])
        stories._compute_task_sla()

    # ✅ FIXED NAME + batching + safe email
    @api.model
    def _cron_story_sla_email(self):

        domain = [
            ('is_done', '=', False),
            ('planned_end_date', '!=', False),
            ('sla_stage', 'in', ['amber', 'red', 'red_3', 'red_6']),
        ]

        batch_size = 200
        offset = 0

        template_map = {
            'amber': 'project_main_mgmt.email_template_story_sla_amber',
            'red': 'project_main_mgmt.email_template_story_sla_red',
            'red_3': 'project_main_mgmt.email_template_story_sla_red_3',
            'red_6': 'project_main_mgmt.email_template_story_sla_red_6',
        }

        # ✅ STEP 1: Get the authorized sender from System Settings or Company
        # This replaces the hardcoded 'Gmail SMTP' search
        authorized_email = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )

        while True:
            stories = self.search(domain, limit=batch_size, offset=offset)
            if not stories:
                break

            offset += batch_size

            for story in stories:
                try:
                    stage = story.sla_stage

                    # prevent duplicate
                    if story.sla_last_notified_stage == stage:
                        continue

                    users = self._get_sla_users(story, stage)

                    partners = users.mapped('partner_id').filtered(
                        lambda p: p.email
                    )

                    if not partners:
                        _logger.warning(f"No recipients for story {story.id}")
                        continue

                    template = self.env.ref(
                        template_map.get(stage),
                        raise_if_not_found=False
                    )

                    if not template:
                        _logger.error(f"Missing template for stage {stage}")
                        continue

                    template.send_mail(
                        story.id,
                        force_send=True,
                        email_values={
                            'email_from': authorized_email,
                            'recipient_ids': [(6, 0, partners.ids)],
                        }
                    )

                    story.sla_last_notified_stage = stage
                    story.sla_last_notified_date = fields.Date.today()

                except Exception:
                    _logger.exception(f"SLA email failed for story {story.id}")

    def _get_sla_users(self, story, stage):

        if stage == 'amber':
            return story.sla_amber_user_ids

        elif stage == 'red':
            return story.sla_red_user_ids

        elif stage == 'red_3':
            return story.sla_overdue_3_user_ids

        elif stage == 'red_6':
            return story.sla_overdue_6_user_ids

        return self.env['res.users']
##############################################
    def _current_user_is_follower_with_subtype(self, subtype_xmlid):
        self.ensure_one()

        partner = self.env.user.partner_id
        if not partner:
            return False

        subtype = self.env.ref(subtype_xmlid, raise_if_not_found=False)
        if not subtype:
            return False

        follower = self.env['mail.followers'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('partner_id', '=', partner.id),
        ], limit=1)

        if not follower:
            return False

        return subtype.id in follower.subtype_ids.ids

    def _current_user_has_kanban_drag_access(self):
        self.ensure_one()

        if self._is_full_project_manager_access():
            return True

        # story-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_user_story_kanban_drag_access'
        ):
            return True

        # fallback to project-level access
        project = self.project_id or (self.epic_id.project_id if self.epic_id else False)
        return bool(project and project._current_user_has_kanban_drag_access())

    def _current_user_has_governance_access(self):
        self.ensure_one()

        if self._is_full_project_manager_access():
            return True

        # story-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_user_story_governance_access'
        ):
            return True

        # fallback to project-level access
        project = self.project_id or (self.epic_id.project_id if self.epic_id else False)
        return bool(project and project._current_user_has_governance_access())

    def _current_user_has_deadline_change_access(self):
        self.ensure_one()

        if self._is_full_project_manager_access():
            return True

        # story-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_user_story_deadline_access'
        ):
            return True

        # fallback to project-level access
        project = self.project_id or (self.epic_id.project_id if self.epic_id else False)
        return bool(project and project._current_user_has_deadline_change_access())

    def check_access_rule(self, operation):
        if operation in ('write', 'unlink'):
            for rec in self:
                # Admin / Program Manager / Project Manager
                if rec._is_full_project_manager_access():
                    continue

                # Allow assigned approver only for approval button flow
                if (
                        operation == 'write'
                        and self.env.context.get('from_story_approval')
                        and rec._is_current_user_story_approver()
                ):
                    continue

                # Allow kanban drag users
                if operation == 'write' and rec._current_user_has_kanban_drag_access():
                    continue

                break
            else:
                return

        return super().check_access_rule(operation)

    access_user_ids = fields.Many2many(
        'res.users',
        'project_story_access_user_rel',
        'story_id',
        'user_id',
        string="Access Users",
        compute='_compute_access_user_ids',
        store=True,
    )

    @api.depends('message_partner_ids', 'project_id.access_user_ids')
    def _compute_access_user_ids(self):
        for rec in self:
            users = self.env['res.users']
            users |= rec.message_partner_ids.mapped('user_ids')
            if rec.project_id:
                users |= rec.project_id.access_user_ids
            rec.access_user_ids = [(6, 0, users.ids)]

