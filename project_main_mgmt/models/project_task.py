from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError,AccessError
from datetime import timedelta
import logging


_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = ["project.task", 'hierarchy.sequence.mixin', 'scheduler.mixin']

    story_id = fields.Many2one(
        'project.user.story',
        string="User Story",
        index=True,
        ondelete='cascade'
    )
    epic_id = fields.Many2one(
        'project.epic',
        string="Epic",
        compute="_compute_epic_id",
        store=True,
        readonly=True
    )
    code = fields.Char(readonly=True)
    sequence_no = fields.Integer(readonly=True)
    enable_backlog_flow = fields.Boolean(
        related='project_id.enable_backlog_flow',
        store=False,
        readonly=True
    )
    # Agile metadata
    weightage = fields.Selection(
        [(str(i), str(i)) for i in range(1, 11)],
        string="Task Weightage",

    )
    estimate = fields.Float(string="Work Hours (Hours)")
    expected_end_date = fields.Date(string="Expected End Date", readonly=True)

    # Blocking
    is_blocked = fields.Boolean(string="Blocked")
    block_reason = fields.Text(string="Block Reason")

    # SLA
    sla_due_date = fields.Date(string="SLA Due Date")
    # ✅ THIS IS THE MISSING FIELD CAUSING YOUR ERROR
    subtask_ids = fields.One2many(
        'project.subtask',
        'task_id',
        string="Subtasks"
    )
    # In your project.task model
    closed_subtask_count = fields.Integer(compute='_compute_subtask_count')
    # 1. Collaborative Description (Overriding native description)
    # description = fields.Html(
    #     string="Description",
    #     sanitize_attributes=False,
    #     wrapper_tag='div',
    #     tracking=True
    # )

    # 2. Document Fields
    document_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_document_ids',
        inverse='_inverse_document_ids',
        string="Documents"
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
        string="Document Count"
    )

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
        ('done', 'Complete'),
        ('cancelled', 'Cancelled'),
    ], default='new', tracking=True)

    inherited_notes = fields.Html(
        compute="_compute_inherited_notes",
        sanitize=False
    )

    assignee_id = fields.Many2one(
        'res.users',
        required=True,
        tracking=True
    )
    task_label_id = fields.Many2one(
        'project.task.label.master',
        string="Task Label",
        domain="[('applies_to','=','task')]"
    )

    # 18/1/2026
    sla_risk = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red'),
        ],
        string="SLA Risk",
        compute="_compute_subtask_sla",
        store=True,
    )

    sla_escalation_rules = fields.Text(
        string="SLA Escalation Rules"
    )

    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'task_sla_amber_rel',
        'task_id',
        'user_id',
        string="Amber Escalation Owners"
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'task_sla_red_rel',
        'task_id',
        'user_id',
        string="Red Escalation Owners"
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'task_sla_overdue3_rel',
        'task_id',
        'user_id',
        string="Overdue +3 Days Owners"
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'task_sla_overdue6_rel',
        'task_id',
        'user_id',
        string="Overdue +6 Days Owners"
    )

    sla_state = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red'),
        ],
        string="SLA Status",
        compute="_compute_subtask_sla",
        store=True,
    )

    sla_days_remaining = fields.Integer(
        string="Days Remaining / Overdue",
        compute="_compute_subtask_sla",
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
        compute="_compute_subtask_sla",
        store=True,
        # group_expand='_group_expand_sla_stage'
    )

    # @api.model
    # def _group_expand_sla_stage(self, stages, domain):
    #     return ['green', 'amber', 'red', 'red_3', 'red_6']

    planned_start_date = fields.Date(string="Planned Start Date")
    planned_end_date = fields.Date(string="Planned End Date")
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
        copy=False
    )

    priorities = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="Priority", default='low')

    category = fields.Selection(
        related='project_id.category',
        store=False,
        readonly=True,
    )

    sla_days_label = fields.Char(
        string="SLA Days",
        compute="_compute_sla_days_label",
        store=True,
    )

    task_type_id = fields.Many2one(
        'project.task.type.master',
        string="Task Type",
        domain="[('applies_to','=','task')]"
    )

    allow_timesheet_user_ids = fields.Many2many(
        'res.users',
        'project_task_timesheet_user_rel',  # ✅ UNIQUE TABLE NAME
        'task_id',  # column 1
        'user_id',  # column 2
        string="Allowed Timesheet Users"
    )

    last_review_reminder_date = fields.Date(copy=False)
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
        return 'story_id'

    @api.depends('planned_end_date', 'is_done')
    def _compute_subtask_sla(self):
        today = fields.Date.today()

        for task in self:

            if task.is_done:
                task.sla_risk = 'green'
                task.sla_state = 'green'
                task.sla_stage = 'green'
                task.sla_days_remaining = 0
                continue

            if not task.planned_end_date:
                task.sla_risk = 'green'
                task.sla_state = 'green'
                task.sla_stage = 'green'
                task.sla_days_remaining = 0
                continue

            delta_days = (task.planned_end_date - today).days
            task.sla_days_remaining = delta_days

            # SLA Risk
            if delta_days > 3:
                task.sla_risk = 'green'
                task.sla_state = 'green'
                task.sla_stage = 'green'

            elif 0 < delta_days <= 3:
                task.sla_risk = 'amber'
                task.sla_state = 'amber'
                task.sla_stage = 'amber'

            elif 0 >= delta_days > -3:
                task.sla_risk = 'red'
                task.sla_state = 'red'
                task.sla_stage = 'red'

            elif -3 >= delta_days > -6:
                task.sla_risk = 'red'
                task.sla_state = 'red'
                task.sla_stage = 'red_3'

            else:
                task.sla_risk = 'red'
                task.sla_state = 'red'
                task.sla_stage = 'red_6'

    def action_open_subtask_sla_7_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=7)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Subtasks - Next 7 Days',
            'res_model': 'project.subtask',  # 🔥 THIS IS THE FIX
            'view_mode': 'list,form',
            'domain': [
                ('task_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('status', '!=', 'done'),
            ],
        }

    def action_open_subtask_sla_30_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=30)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Subtasks - Next 30 Days',
            'res_model': 'project.subtask',  # 🔥 MUST BE THIS
            'view_mode': 'list,form',
            'domain': [
                ('task_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('status', '!=', 'done'),
            ],
        }

    # def action_open_sla_monitoring(self):
    #     self.ensure_one()
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'SLA Monitoring',
    #         'res_model': 'project.subtask',
    #         'view_mode': 'kanban,list,form',
    #         'domain': [
    #             ('task_id', '=', self.id),
    #             ('status', '!=', 'done'),
    #         ],
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #     }

    def action_open_sla_monitoring(self):
        self.ensure_one()

        kanban_view = self.env.ref(
            'project_main_mgmt.view_subtask_sla_kanban'
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': 'project.subtask',

            # 🔥 FORCE your custom kanban view
            # open SLA kanban first
            'views': [
                (kanban_view.id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],

            'domain': [
                ('task_id', '=', self.id),
                # ('status', '!=', 'done'),
            ],
            'context': {
                'group_by': ['sla_stage'],
            },
        }

    #############################
    #################assignee notify email#####################

    # def action_send_assignment_email(self):
    #     template = self.env.ref('project_main_mgmt.email_template_task_assignment')
    #
    #     for task in self:
    #         if task.assignee_id and task.assignee_id.partner_id:
    #             # 1️⃣ Send email
    #             template.send_mail(task.id, force_send=True)
    #
    #             # 2️⃣ Log in chatter
    #             task.message_post(
    #                 body=f"Task assigned to {task.assignee_id.name}",
    #                 partner_ids=[task.assignee_id.partner_id.id],
    #                 message_type='notification',
    #             )

    def _send_assignment_notification(self):
        template = self.env.ref(
            'project_main_mgmt.email_template_task_assignment',
            raise_if_not_found=False
        )

        if not template:
            return

        for task in self:
            user = task.assignee_id
            partner = user.partner_id if user else False

            if not partner or not partner.email:
                _logger.warning(f"Skipping task {task.id} - no email")
                continue

            mail_server = self.env['ir.mail_server'].search([], limit=1)

            smtp_user = mail_server.smtp_user if mail_server else None

            template.sudo().send_mail(
                task.id,
                force_send=True,
                email_values={
                    'email_to': partner.email,
                    'email_from': smtp_user,  # 🔥 CRITICAL FIX
                }
            )
    ############################################################
    @api.model_create_multi
    def create(self, vals_list):





        # 0️⃣ NORMALIZE story field (CRITICAL)
        # UI often sends user_story_id, not story_id
        for vals in vals_list:
            if not vals.get('story_id') and vals.get('user_story_id'):
                vals['story_id'] = vals['user_story_id']

        # 1️⃣ Ensure project_id for record rules
        for vals in vals_list:
            if not vals.get('project_id') and vals.get('story_id'):
                story = self.env['project.user.story'].browse(vals['story_id'])
                if story.project_id:
                    vals['project_id'] = story.project_id.id

            # 🔥 FLOW VALIDATION (ADD ONLY - keep old logic below)
        for vals in vals_list:
            story_id = vals.get('story_id') or self.env.context.get('default_story_id')
            project_id = vals.get('project_id') or self.env.context.get('default_project_id')

            # If no project at all, skip validation (other Odoo modules / internal task creation)
            if not project_id and not story_id:
                continue

            # Resolve project from story if needed
            story = False
            if story_id:
                story = self.env['project.user.story'].browse(story_id)
                project = story.project_id or story.epic_id.project_id
            else:
                project = self.env['project.project'].browse(project_id) if project_id else False

            # If no project resolved, skip validation (safe for other modules)
            if not project:
                continue

            # 🔥 Apply validation ONLY for your custom managed projects
            # If toggle ON or OFF exists, this is your custom project flow project
            if not hasattr(project, 'enable_backlog_flow'):
                continue

            # Task in your project flow must come only from User Story
            if not story_id:
                raise ValidationError(_(
                    "Task must be created only from User Story.\n\n"
                    "Valid flow:\n"
                    "Toggle ON  → Project → Product Backlog → Epic → User Story → Task → Subtask\n"
                    "Toggle OFF → Project → User Story → Task → Subtask"
                ))

            # Extra flow validation
            if project.enable_backlog_flow and not story.epic_id:
                raise ValidationError(_(
                    "When 'Enable Backlog & Epic' is ON, Task can be created only from a User Story under Epic."
                ))

            if not project.enable_backlog_flow and story.epic_id:
                raise ValidationError(_(
                    "When 'Enable Backlog & Epic' is OFF, Task can be created only from a direct Project User Story."
                ))

            # 🔥 ADD HERE (Governance access check)
        # if not self.env.user.has_group('base.group_system'):
        #     for vals in vals_list:
        #         project = False
        #
        #         if vals.get('project_id'):
        #             project = self.env['project.project'].browse(vals['project_id'])
        #         elif vals.get('story_id'):
        #             story = self.env['project.user.story'].browse(vals['story_id'])
        #             project = story.project_id
        #
        #         if project:
        #
        #             if vals.get('approver_ids') and not project._current_user_has_governance_access():
        #                 raise AccessError(_("You do not have Governance access for this project."))
        #
        #             if (vals.get('planned_start_date') or vals.get('planned_end_date')) \
        #                     and not project._current_user_has_deadline_change_access():
        #                 raise AccessError(_("You do not have Changing Deadline access for this project."))
        #

        # ✅ Governance access (Updated for Task Followers)
        if (not self.env.context.get('skip_task_governance_check') and
                any(k in vals for k in ['approver_ids', 'approved_by_id', 'is_done', 'evidence_required'])):

            for rec in self:
                # Check if user is full manager
                if rec._is_full_project_manager_access():
                    continue

                # Check if user is a task follower
                is_task_follower = self.env.user.partner_id in rec.message_partner_id_ids

                # Check if user is an assigned approver
                is_approver = rec._is_current_user_task_approver()

                # Allow access if they are an approver OR a task follower (if you want followers to have gov access)
                if not (is_approver or is_task_follower):
                    raise AccessError("You do not have Governance access for this task.")

        # 2️⃣ Create (sudo only if governed)
        if self.env.context.get('story_governed_create'):
            tasks = super(ProjectTask, self.sudo()).create(vals_list)
        else:
            tasks = super().create(vals_list)

        # 3️⃣ Code + sequence + prefix
        for task in tasks:

            # SUBTASK
            if task.parent_id:
                seq = task._next_sequence([
                    ('parent_id', '=', task.parent_id.id),
                ])
                task.sequence_no = seq
                task.code = f"{task.parent_id.code}-ST{seq}"

            # TASK under USER STORY
            elif task.story_id:
                seq = task._next_sequence([
                    ('story_id', '=', task.story_id.id),
                    ('parent_id', '=', False),
                ])
                task.sequence_no = seq
                task.code = f"{task.story_id.code}-T{seq}"

            else:
                continue

            # Prefix name ONCE
            if task.name and not task.name.startswith(task.code):
                task.name = f"{task.code} - {task.name}"

            # 🔥 ADD THIS ONLY
            # 🔥 ADD THIS BLOCK
            # 🔥🔥🔥 VERY IMPORTANT BLOCK (OUTSIDE LOOP)
        # for task in tasks:
        #     if task.stage_id:
        #         task.task_progress = task.stage_id.progress or 0
        for task in tasks:
            if task.stage_id:
                if hasattr(task.stage_id, 'count_in_progress') and not task.stage_id.count_in_progress:
                    task.task_progress = 0
                else:
                    task.task_progress = max(0, min(100, task.stage_id.progress or 0))

        # 🔥 NEW: Send notification for new assignments
        for task in tasks:
            if task.assignee_id:
                task._send_assignment_notification()

        return tasks

    def write(self, vals):

        if self.env.context.get('skip_scheduler_chain'):
            return super(ProjectTask, self).write(vals)
        if self.env.context.get('from_timer') or self.env.context.get('from_timer_create'):
            return super(ProjectTask, self).write(vals)
        if any([
            self.env.context.get('from_timer'),
            self.env.context.get('from_timer_create'),
            self.env.context.get('tracking_disable'),
            self.env.context.get('mail_notrack'),
        ]):
            return super(ProjectTask, self).write(vals)

        if not self.env.context.get('skip_task_readonly_check'):

            # allow subtask creation, timer, timesheet
            safe_fields = {
                # timer core
                'timer_state',
                'timer_running',
                'task_start_date',
                'task_accumulated_time',
                'is_timer_running',
                'user_timer_id',
                'display_timer',

                # timesheet linkage
                'timesheet_ids',
                'account_analytic_line_ids',

                # internal writes (CRITICAL)
                'date_last_stage_update',
                'planned_hours',
                'remaining_hours',
                'effective_hours',

                # chatter (timer logs)
                'message_ids',
                'message_follower_ids',
                'message_partner_ids',

                # technical
                'write_date',
                'write_uid',
            }
            if not set(vals.keys()).issubset(safe_fields):
                self._check_task_readonly_access(vals)

        # 🔹 Sync kanban state BEFORE write
        # Sync kanban state BEFORE write
        if 'status' in vals:
            vals['kanban_state'] = vals['status']


        is_kanban_drag = any(k in vals for k in [
            'stage_id',
            'status',
            'kanban_state',
            'state',
            'sequence',
            'date_last_stage_update'
        ])
        # ✅ Kanban drag access
        if (not self.env.context.get('skip_task_kanban_check') and is_kanban_drag):
            for rec in self:
                if rec._is_full_project_manager_access():
                    continue

                if (
                        self.env.context.get('from_task_approval')
                        and rec._is_current_user_task_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'stage_id', 'status', 'kanban_state'
                })
                ):
                    continue

                if not rec._current_user_has_kanban_drag_access():
                    raise AccessError(_("You do not have Kanban Drag & Drop access for this task."))

            # ✅ Governance access
        # if (
        #         not self.env.context.get('skip_task_governance_check')
        #         and any(k in vals for k in [
        #     'approver_ids',
        #     'approved_by_id',
        #     'is_done',
        #     'evidence_required'
        # ])
        # ):
        #     for rec in self:
        #         if rec._is_full_project_manager_access():
        #             continue
        #
        #         if (
        #                 self.env.context.get('from_task_approval')
        #                 and rec._is_current_user_task_approver()
        #                 and set(vals.keys()).issubset({
        #             'is_done', 'approved_by_id', 'completed_date', 'stage_id', 'status', 'kanban_state'
        #         })
        #         ):
        #             continue
        #
        #         # if not rec._is_current_user_task_approver():
        #         #     raise AccessError("You do not have Governance access for this task.")
        #
        #         if not rec._current_user_has_governance_access():
        #             raise AccessError(_("You do not have Governance access for this task."))

        # ✅ Governance access validation
        if (not self.env.context.get('skip_task_governance_check') and
                any(k in vals for k in ['approver_ids', 'approved_by_id', 'is_done', 'evidence_required'])):

            for rec in self:
                # 1. 🚀 DYNAMIC MANAGER BYPASS
                # Check if current user is the Project Manager, Program Manager, or in the Admin Group
                is_manager = (
                        self.env.user.has_group('project.group_project_manager') or
                        self.env.user.id == rec.project_id.user_id.id or
                        self.env.user.id == rec.project_id.program_manager_id.id or
                        rec._is_full_project_manager_access()
                )

                # If they are a manager, they can give access to anyone (skip the error)
                if is_manager:
                    continue

                # 2. FOR NON-MANAGERS (Workers/Followers)
                # Check if they are already an approver or a task follower
                is_task_follower = self.env.user.partner_id in rec.message_partner_ids
                is_approver = rec._is_current_user_task_approver()
                has_gov_rights = rec._current_user_has_governance_access()

                if not (is_approver or is_task_follower or has_gov_rights):
                    raise AccessError(
                        _("You do not have Governance access for this task. Only Managers or Governance members can modify these fields."))

            # ... rest of your write method ...
            return super(ProjectTask, self).write(vals)


        # Deadline access
        if 'planned_start_date' in vals or 'planned_end_date' in vals:
            if not (
                    self.env.context.get('from_kanban_drag_auto')
                    or self.env.context.get('skip_scheduler_chain')
                    or self.env.context.get('skip_deadline_access_check')
                    or (
                            is_kanban_drag and all(
                        task.project_id and task.project_id._current_user_has_kanban_drag_access()
                        for task in self
                    )
                    )
            ):
                self._check_project_follower_deadline_access()



        # 🔥 NEW: Check if assignee is being changed
        assignee_changed = 'assignee_id' in vals and vals.get('assignee_id') != self.assignee_id.id

        # 🔹 Sync kanban state BEFORE write
        if 'status' in vals:
            vals['kanban_state'] = vals['status']

        # 🔥 Validate total = 100 only when moving to Done stage
        if 'stage_id' in vals:
            self._check_stage_progress_total_is_100(vals['stage_id'])

        # 🔥 Single super call
        res = super(ProjectTask, self).write(vals)

        # ---------- AFTER WRITE ----------
        if 'stage_id' in vals:
            stage_obj = self.env['project.task.type']

            for rec in self:
                new_stage = rec.stage_id

                if not new_stage:
                    continue

                # 🔹 If moved to Cancelled / non-progress stage → force 0
                if hasattr(new_stage, 'count_in_progress') and not new_stage.count_in_progress:
                    super(ProjectTask, rec).write({
                        'task_progress': 0
                    })
                    continue

                # 🔹 Prefer project-specific stages first
                project_stages = stage_obj.search([
                    ('count_in_progress', '=', True),
                    ('project_ids', 'in', rec.project_id.id),
                    ('sequence', '<=', new_stage.sequence)
                ], order='sequence')

                # 🔹 Else fallback to global stages
                if project_stages:
                    stages = project_stages
                else:
                    stages = stage_obj.search([
                        ('count_in_progress', '=', True),
                        ('project_ids', '=', False),
                        ('sequence', '<=', new_stage.sequence)
                    ], order='sequence')

                progress_total = sum(stages.mapped('progress'))

                # 🔹 Safety cap
                progress_total = max(0, min(100, progress_total))

                # 🔥 Update progress safely
                super(ProjectTask, rec).write({
                    'task_progress': progress_total
                })
                # 🔥 Immediately auto move to folded done stage when progress = 100
                if not (self.env.context.get('skip_auto_done_stage') or self.env.context.get('from_kanban_drag_auto')):
                    rec._auto_move_to_done_stage_when_progress_100()

        # 🔹 Handle rename logic AFTER everything
        if 'name' in vals:
            for task in self:
                if task.code and task.name and not task.name.startswith(task.code):
                    super(ProjectTask, task).write({
                        'name': f"{task.code} - {task.name}"
                    })

        # 🔥 Auto move to folded done stage when progress reaches 100
        if not (self.env.context.get('skip_auto_done_stage') or self.env.context.get(
                'from_kanban_drag_auto')):
            self._auto_move_to_done_stage_when_progress_100()

        # 🔥 NEW: Send notification if assignee was updated
        if assignee_changed:
            self._send_assignment_notification()

        return res

    def _check_stage_progress_total_is_100(self, new_stage_id):
        stage_obj = self.env['project.task.type']
        new_stage = stage_obj.browse(new_stage_id)

        for rec in self:
            # Only validate when moving to Done / folded workflow stage
            if not new_stage or not new_stage.fold:
                continue

            # Skip non-progress stages like Cancelled
            if hasattr(new_stage, 'count_in_progress') and not new_stage.count_in_progress:
                continue

            # 🔹 Prefer project-specific workflow stages first
            project_stages = stage_obj.search([
                ('count_in_progress', '=', True),
                ('project_ids', 'in', rec.project_id.id)
            ], order='sequence')

            # 🔹 Else fallback to global workflow stages
            if project_stages:
                stages = project_stages
            else:
                stages = stage_obj.search([
                    ('count_in_progress', '=', True),
                    ('project_ids', '=', False)
                ], order='sequence')

            total = sum(stages.mapped('progress'))

            if total != 100:
                raise ValidationError(
                    f"Total workflow task stage progress must be exactly 100 before moving to Done stage. "
                    f"Current total is {total}."
                )

    # @api.depends(
    #     'story_id.connextra_story',  # Fix dependency name here
    #     'story_id.epic_id.description',
    #     'story_id.epic_id.backlog_id.description',
    #     'story_id.epic_id.backlog_id.project_id.description'
    # )
    # def _compute_inherited_notes(self):
    #     for rec in self:
    #         story = rec.story_id.sudo() if rec.story_id else False
    #         epic = story.epic_id.sudo() if story and story.epic_id else False
    #         backlog = epic.backlog_id.sudo() if epic and epic.backlog_id else False
    #         project = backlog.project_id.sudo() if backlog and backlog.project_id else False
    #
    #         # Use connextra_story for the User Story level
    #         story_note = story.connextra_story or "" if story else ""
    #         epic_note = epic.description or "" if epic else ""
    #         backlog_note = backlog.description or "" if backlog else ""
    #         project_note = project.description or "" if project else ""
    #
    #         sections = []
    #         if project_note:
    #             sections.append(f"<h4>Project Notes</h4>{project_note}<hr/>")
    #         if backlog_note:
    #             sections.append(f"<h4>Backlog Notes</h4>{backlog_note}<hr/>")
    #         if epic_note:
    #             sections.append(f"<h4>Epic Notes</h4>{epic_note}<hr/>")
    #         if story_note:
    #             sections.append(f"<h4>User Story Notes</h4>{story_note}")
    #
    #         rec.inherited_notes = "".join(sections)

    @api.depends(
        'story_id.connextra_story',
        'story_id.project_id.description',
        'story_id.project_id.enable_backlog_flow',
        'story_id.epic_id.description',
        'story_id.epic_id.backlog_id.description',
        'story_id.epic_id.backlog_id.project_id.description',
        'story_id.epic_id.backlog_id.project_id.enable_backlog_flow'
    )
    def _compute_inherited_notes(self):
        for rec in self:
            story = rec.story_id.sudo() if rec.story_id else False
            epic = story.epic_id.sudo() if story and story.epic_id else False
            backlog = epic.backlog_id.sudo() if epic and epic.backlog_id else False

            project = (
                story.project_id.sudo()
                if story and story.project_id
                else (backlog.project_id.sudo() if backlog and backlog.project_id else False)
            )

            story_note = story.connextra_story or "" if story else ""
            epic_note = epic.description or "" if epic else ""
            backlog_note = backlog.description or "" if backlog else ""
            project_note = project.description or "" if project else ""

            sections = []

            if project_note:
                sections.append(f"<h4>Project Notes</h4>{project_note}<hr/>")

            if project and project.enable_backlog_flow:
                if backlog_note:
                    sections.append(f"<h4>Backlog Notes</h4>{backlog_note}<hr/>")
                if epic_note:
                    sections.append(f"<h4>Epic Notes</h4>{epic_note}<hr/>")

            if story_note:
                sections.append(f"<h4>User Story Notes</h4>{story_note}")

            rec.inherited_notes = "".join(sections)

    # def action_mark_done(self):
    #     self.ensure_one()
    #
    #     # Already approved → do nothing
    #     if self.is_done:
    #         return
    #
    #     # 1️⃣ Permission check
    #     if self.env.user not in self.approver_ids:
    #         raise UserError("You are not authorized to approve this task.")
    #
    #     # 2️⃣ Block if ANY subtask not complete
    #     pending = self.env['project.subtask'].search_count([
    #         ('task_id', '=', self.id),
    #         ('status', '!=', 'done'),
    #     ])
    #     if pending:
    #         raise ValidationError(
    #             "All subtasks must be completed before approving this task."
    #         )
    #
    #     # 3️⃣ Find DONE stage (folded stage)
    #     done_stage = self.env['project.task.type'].search([
    #         ('fold', '=', True),
    #         '|',
    #         ('project_ids', '=', False),
    #         ('project_ids', 'in', self.project_id.id),
    #     ], limit=1)
    #
    #     if not done_stage:
    #         raise ValidationError("No Done stage found for this project.")
    #
    #     # 4️⃣ GOVERNANCE APPROVAL — UPDATE ALL REQUIRED FIELDS
    #     self.sudo().write({
    #         # Governance
    #         'is_done': True,
    #         'approved_by_id': self.env.user.id,
    #
    #         # Workflow
    #         # 'stage_id': done_stage.id,
    #
    #         # ✅ FIXED FOR ODOO 19: The key is '1_done', not 'done'
    #         'state': '1_done',
    #
    #         # Your custom business fields
    #         'status': 'done',
    #
    #         # This sets the Green Dot (High Priority/Ready)
    #         'kanban_state': 'done',
    #     })

    def _is_current_user_task_approver(self):
        self.ensure_one()
        return self.env.user in self.approver_ids

    # def action_mark_done(self):
    #     self.ensure_one()
    #
    #
    #     if self.is_done:
    #         return
    #
    #     # 1️⃣ Approver check
    #     if self.env.user not in self.approver_ids:
    #         raise UserError("You are not authorized to approve this task.")
    #
    #     # 2️⃣ Check all subtasks completed
    #     pending_subtasks = self.env['project.subtask'].search_count([
    #         ('task_id', '=', self.id),
    #         ('status', '!=', 'done'),
    #     ])
    #
    #     if pending_subtasks:
    #         raise ValidationError(
    #             "All subtasks must be completed before approving this task."
    #         )
    #
    #     # 3️⃣ Get last stage except Cancel
    #     # stages = self.project_id.type_ids.filtered(
    #     #     lambda s: 'cancel' not in (s.name or '').lower()
    #     # ).sorted(key=lambda s: s.sequence)
    #     #
    #     # last_stage = stages[-1] if stages else False
    #     #
    #     # if not last_stage:
    #     #     raise ValidationError("No valid stage found for this project.")
    #     stages = self.project_id.type_ids.filtered(
    #         lambda s: 'cancel' not in (s.name or '').lower()
    #     ).sorted(key=lambda s: s.sequence)
    #
    #     done_stage = False
    #     total_progress = 0
    #
    #     for stage in stages:
    #         total_progress += stage.progress or 0
    #         if total_progress >= 100:
    #             done_stage = stage
    #             break
    #
    #     if not done_stage:
    #         raise ValidationError("No valid done stage found where cumulative progress reaches 100%.")
    #     # 4️⃣ Governance approval
    #     # 4️⃣ Approver can approve without Kanban Drag access
    #     self.with_context(
    #         skip_task_readonly_check=True,
    #         skip_task_kanban_check=True,
    #         skip_task_governance_check=True,
    #         skip_deadline_access_check=True,
    #         skip_auto_done_stage=True,
    #         from_task_approval=True,
    #     ).write({
    #         'is_done': True,
    #         'approved_by_id': self.env.user.id,
    #         'completed_date': fields.Datetime.now(),
    #         'stage_id': done_stage.id,
    #         'status': 'done',
    #         'kanban_state': 'done'
    #     })

    def action_mark_done(self):
        self.ensure_one()
        if self.is_done:
            return

        # 1️⃣ Governance & Approver Check
        # We use .sudo() because the worker might not have 'read' access to the project record
        project_sudo = self.project_id.sudo()

        is_approver = self.env.user in self.approver_ids
        # Check if user has the custom 'Governance' access defined on the project
        has_governance = project_sudo._current_user_has_governance_access()

        if not is_approver:
            raise UserError("You are not in the Approvers list for this task.")

        if not has_governance:
            raise AccessError(
                "You do not have Governance access for this project. Only authorized Governance members can approve tasks.")

        # 2️⃣ Check all subtasks completed
        pending_subtasks = self.env['project.subtask'].sudo().search_count([
            ('task_id', '=', self.id),
            ('status', '!=', 'done'),
        ])
        if pending_subtasks:
            raise ValidationError("All subtasks must be completed before approving this task.")

        # 3️⃣ Logic to find the 'Done' stage (using sudo)
        stages = project_sudo.type_ids.filtered(
            lambda s: 'cancel' not in (s.name or '').lower()
        ).sorted(key=lambda s: s.sequence)

        done_stage = False
        total_progress = 0
        for stage in stages:
            total_progress += stage.progress or 0
            if total_progress >= 100:
                done_stage = stage
                break

        if not done_stage:
            raise ValidationError("No valid done stage found where cumulative progress reaches 100%.")

        # 4️⃣ Execute the Approval
        self.with_context(
            skip_task_readonly_check=True,
            skip_task_kanban_check=True,
            skip_task_governance_check=True,
            from_task_approval=True,
        ).write({
            'is_done': True,
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
            'stage_id': done_stage.id,
            'status': 'done',
            'kanban_state': 'done'
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

    # 3. Document Action
    def action_view_task_documents(self):
        self.ensure_one()
        return {
            'name': 'Task Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
            'target': 'current',
        }

    @api.depends('subtask_ids', 'subtask_ids.status')
    def _compute_subtask_count(self):
        for rec in self:
            # 1. Always initialize the fields to 0 first
            rec.subtask_count = len(rec.subtask_ids)
            rec.closed_subtask_count = 0

            # 2. Logic for closed tasks
            if rec.subtask_ids:
                closed = rec.subtask_ids.filtered(lambda s: s.status == 'done')
                rec.closed_subtask_count = len(closed)

    # def action_view_subtasks(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Subtasks',
    #         'res_model': 'project.subtask',
    #         'view_mode': 'list,form',
    #         'domain': [('task_id', '=', self.id)],
    #         'context': {
    #             'default_task_id': self.id,
    #             'default_project_id': self.project_id.id,
    #             'default_story_id': self.story_id.id,
    #         },
    #     # }
    def action_view_subtasks(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Subtasks',
            'res_model': 'project.subtask',

            # 🔥 all views visible
            'view_mode': 'kanban,list,form,timeline,activity,pivot,graph,calendar',

            # ❌ REMOVE 'views': []
            # very important

            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
                'default_story_id': self.story_id.id,
            }
        }

    @api.depends('story_id', 'story_id.epic_id')
    def _compute_epic_id(self):
        for task in self:
            task.epic_id = task.story_id.epic_id if task.story_id else False

    @api.onchange('story_id')
    def _onchange_story_id(self):
        if self.story_id:
            self.project_id = self.story_id.project_id

    #
    # def write(self, vals):
    #     if 'status' in vals:
    #         vals['kanban_state'] = vals['status']
    #     return super().write(vals)
    #
    # @api.model
    # def create(self, vals):
    #     # Governance-based task creation from User Story
    #     if self.env.context.get('story_governed_create'):
    #         return super(ProjectTask, self.sudo()).create(vals)
    #     return super().create(vals)

    subtask_progress = fields.Float(
        related='subtask_ids.subtask_progress',
        string="Progress %",
        readonly=True
    )

    task_subtask_avg = fields.Float(
        string="Subtask Avg %",
        compute="_compute_subtask_avg",
        store=True
    )

    @api.depends('subtask_ids.subtask_progress')
    def _compute_subtask_avg(self):
        for task in self:
            if task.subtask_ids:
                vals = task.subtask_ids.mapped('subtask_progress')
                task.task_subtask_avg = sum(vals) / len(vals)
            else:
                task.task_subtask_avg = 0

    # task stage
    task_progress = fields.Float("Task Progress %", default=0)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Already resolved → do nothing
        if res.get('story_id'):
            return res

        ctx = self.env.context

        # 🔥 If opened from User Story → auto-attach
        if ctx.get('active_model') == 'project.user.story' and ctx.get('active_id'):
            story = self.env['project.user.story'].browse(ctx['active_id'])
            if story.exists():
                res['story_id'] = story.id
                res['project_id'] = story.project_id.id
                return res

        # Fallback: last project user worked on
        if not res.get('project_id'):
            last_task = self.search(
                [('user_ids', 'in', self.env.user.id)],
                order='id desc',
                limit=1
            )
            if last_task:
                res['project_id'] = last_task.project_id.id

        return res

    progress_color = fields.Char(
        string="Progress Color",
        compute="_compute_progress_color",
        store=False
    )

    @api.depends("task_progress")
    def _compute_progress_color(self):
        # get first config (assuming single master config)
        config = self.env['progress.config'].search([], limit=1)

        lines = config.line_ids.sorted(key=lambda l: l.min_value) if config else []

        for rec in self:
            color = 'bg-primary'  # fallback

            for line in lines:
                if line.min_value <= rec.task_progress <= line.max_value:
                    color = line.color
                    break

            rec.progress_color = color

    def _auto_move_to_done_stage_when_progress_100(self):
        for task in self:
            # Skip if already done
            if task.is_done:
                continue

            # Only act when cumulative progress reaches 100
            if float(task.task_progress or 0.0) < 100:
                continue

            stage_obj = self.env['project.task.type']

            # 🔹 Prefer project-specific workflow stages first
            project_stages = stage_obj.search([
                ('project_ids', 'in', task.project_id.id),
                ('count_in_progress', '=', True),
            ], order='sequence asc')

            # 🔹 Else fallback to global stages
            if project_stages:
                stages = project_stages
            else:
                stages = stage_obj.search([
                    ('project_ids', '=', False),
                    ('count_in_progress', '=', True),
                ], order='sequence asc')

            done_stage = False
            total_progress = 0

            for stage in stages:
                total_progress += stage.progress or 0
                if total_progress >= 100:
                    done_stage = stage
                    break

            if not done_stage:
                continue

            # 🔥 VERY IMPORTANT: auto fold the 100% stage
            if not done_stage.fold:
                done_stage.sudo().write({'fold': True})

            vals = {}

            # Move task to that done stage if not already there
            if task.stage_id != done_stage:
                vals['stage_id'] = done_stage.id

            # Mark business fields done
            if task.status != 'done':
                vals['status'] = 'done'

            if task.kanban_state != 'done':
                vals['kanban_state'] = 'done'

            if not task.completed_date:
                vals['completed_date'] = fields.Datetime.now()

            #         if not task.is_done:
            #             vals['is_done'] = True
            #
            #         if vals:
            #             task.with_context(skip_auto_done_stage=True,from_kanban_drag_auto=True,
            # skip_deadline_access_check=True,).write(vals)
            if vals:
                task.with_context(
                    skip_auto_done_stage=True,
                    from_kanban_drag_auto=True,
                    skip_deadline_access_check=True,
                ).write(vals)

    def _check_project_follower_kanban_drag_access(self):

        for task in self:
            if task._is_full_project_manager_access():
                continue
            project = task.project_id.sudo()
            if project and not project._current_user_has_kanban_drag_access():
                raise AccessError(_("You do not have Kanban Drag & Drop access for this project."))

    def _check_project_follower_governance_access(self):

        for task in self:
            if task._is_full_project_manager_access():
                continue
            project = task.project_id.sudo()
            # if project and not project._current_user_has_governance_access():
            #     raise AccessError(_("You do not have Governance access for this project."))
            return bool(
                self.project_id and self.project_id.sudo()._current_user_has_kanban_drag_access()
            )
    def _check_project_follower_deadline_access(self):

        for task in self:
            # Admin / Program Manager / Project Manager -> full access
            if task._is_full_project_manager_access():
                continue
            project = task.project_id.sudo()
            if not project:
                continue

            if not project._current_user_has_deadline_change_access():
                raise AccessError(_("You do not have Changing Deadline access for this project."))

    def _is_project_user_readonly_mode(self):
        for rec in self:
            if rec._is_full_project_manager_access():
                return False
        return self.env.user.has_group('project.group_project_user')

    def _check_task_readonly_access(self, vals):
        if self.env.context.get('skip_task_readonly_check'):
            return

        if not self._is_project_user_readonly_mode():
            return
        # for rec in self:
        #     if rec._is_full_project_manager_access():
        #         return

        allowed_fields = {

            # chatter
            'subtask_ids',
            'message_follower_ids',
            'message_partner_ids',
            'message_ids',
            'message_main_attachment_id',

            # timesheet
            'timesheet_ids',
            'timesheet_line_ids',
            'account_analytic_line_ids',

            # kanban / stage
            'stage_id',
            'kanban_state',
            'status',
            'state',
            'sequence',
            'date_last_stage_update',

            # deadline
            'planned_start_date',
            'planned_end_date',
            'expected_end_date',
            'completed_date',

            # governance
            'approver_ids',
            'approved_by_id',
            'is_done',
            'evidence_required',

            # 🔥 ADD THESE TIMER FIELDS
            'timer_state',
            'timer_running',
            'task_start_date',
            'task_accumulated_time',
            'is_timer_running',
        }

        technical_ok = {
            'write_date',
            'write_uid',
            '__last_update',
        }

        forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
        if forbidden:
            print("TASK BLOCKED FIELDS:", forbidden)
            raise AccessError(_("Task is read-only. You can only edit Timesheet lines and Chatter."))



    # def _check_task_readonly_access(self, vals):
    #
    #     # --------------------------------------------------
    #     # 1️⃣ HARD BYPASS (SYSTEM / ADMIN / INTERNAL FLOWS)
    #     # --------------------------------------------------
    #     if (
    #             self.env.su
    #             or self.env.user.has_group('base.group_system')
    #             or self.env.context.get('mail_create_nosubscribe')
    #             or self.env.context.get('tracking_disable')
    #             or self.env.context.get('mail_notrack')
    #             or self.env.context.get('install_mode')
    #     ):
    #         return
    #
    #     # --------------------------------------------------
    #     # 2️⃣ APPLY ONLY FOR READONLY USERS
    #     # --------------------------------------------------
    #     if not self._is_project_user_readonly_mode():
    #         return
    #
    #     # --------------------------------------------------
    #     # 3️⃣ ALLOWED FIELDS (EXPANDED FOR ODOO INTERNALS)
    #     # --------------------------------------------------
    #     allowed_fields = {
    #
    #         # chatter
    #         'message_follower_ids',
    #         'message_partner_ids',
    #         'message_ids',
    #         'message_main_attachment_id',
    #         'message_attachment_count',
    #
    #         # timesheet
    #         'timesheet_ids',
    #         'timesheet_line_ids',
    #         'account_analytic_line_ids',
    #
    #         # kanban / stage
    #         'stage_id',
    #         'kanban_state',
    #         'status',
    #         'state',
    #         'sequence',
    #         'date_last_stage_update',
    #
    #         # deadline
    #         'planned_start_date',
    #         'planned_end_date',
    #         'expected_end_date',
    #         'completed_date',
    #
    #         # governance
    #         'approver_ids',
    #         'approved_by_id',
    #         'is_done',
    #         'evidence_required',
    #
    #         # timer
    #         'timer_state',
    #         'timer_running',
    #         'task_start_date',
    #         'task_accumulated_time',
    #         'is_timer_running',
    #
    #         # 🔥 CRITICAL (system writes during user creation)
    #         'user_ids',
    #         'partner_id',
    #         'display_name',
    #         'activity_ids',
    #         'activity_state',
    #         'activity_user_id',
    #     }
    #
    #     # --------------------------------------------------
    #     # 4️⃣ TECHNICAL SAFE FIELDS
    #     # --------------------------------------------------
    #     technical_ok = {
    #         'write_date',
    #         'write_uid',
    #         '__last_update',
    #     }
    #
    #     # --------------------------------------------------
    #     # 5️⃣ BLOCK ONLY IF REALLY FORBIDDEN
    #     # --------------------------------------------------
    #     forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
    #
    #     if forbidden:
    #         _logger.warning("TASK BLOCKED FIELDS: %s", forbidden)
    #         raise AccessError(
    #             _("Task is read-only. You can only edit Timesheet, Chatter, and allowed fields.")
    #         )
    #
    # def _is_full_project_manager_access(self):
    #     self.ensure_one()
    #
    #     project = self.project_id or (self.story_id.project_id if self.story_id else False)
    #
    #     # ✅ admin always allowed
    #     if self.env.user.has_group('base.group_system'):
    #         return True
    #
    #     if not project:
    #         return False
    #
    #     return project._current_user_has_governance_access()
    def _is_full_project_manager_access(self):
        self.ensure_one()

        project = self.project_id or (self.story_id.project_id if self.story_id else False)

        if not project:
            return self.env.user.has_group('base.group_system')

        return project._is_full_project_manager_access()

    ########################################
    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    @api.model
    def _cron_recompute_sla(self):
        tasks = self.search([
            ('planned_end_date', '!=', False),
            ('is_done', '=', False),
        ])
        tasks._compute_subtask_sla()

    @api.model
    def _cron_subtask_sla_email(self):

        domain = [
            ('is_done', '=', False),
            ('planned_end_date', '!=', False),
            ('sla_stage', 'in', ['amber', 'red', 'red_3', 'red_6']),
        ]

        subtasks = self.search(domain)

        template_map = {
            'amber': 'project_main_mgmt.email_template_subtask_sla_amber',
            'red': 'project_main_mgmt.email_template_subtask_sla_red',
            'red_3': 'project_main_mgmt.email_template_subtask_sla_red_3',
            'red_6': 'project_main_mgmt.email_template_subtask_sla_red_6',
        }

        # ✅ Dynamic Sender: No more searching for 'Gmail SMTP' or hardcoded strings
        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )
        for sub in subtasks:
            try:
                stage = sub.sla_stage

                if sub.sla_last_notified_stage == stage:
                    continue

                users = self._get_subtask_sla_users(sub, stage)

                partners = users.mapped('partner_id').filtered(lambda p: p.email)

                _logger.info(f"Subtask {sub.id} | Stage: {stage} | Users: {users.ids}")

                if not partners:
                    _logger.warning(f"No recipients for subtask {sub.id}")
                    continue

                template = self.env.ref(template_map.get(stage))

                template.send_mail(
                    sub.id,
                    force_send=True,
                    email_values={
                        'email_from': email_from,
                        'recipient_ids': [(6, 0, partners.ids)],
                    }
                )

                sub.sla_last_notified_stage = stage
                sub.sla_last_notified_date = fields.Date.today()

            except Exception:
                _logger.exception(f"SLA email failed for subtask {sub.id}")

    def _get_subtask_sla_users(self, subtask, stage):

        if stage == 'amber':
            return subtask.sla_amber_user_ids
        elif stage == 'red':
            return subtask.sla_red_user_ids
        elif stage == 'red_3':
            return subtask.sla_overdue_3_user_ids
        elif stage == 'red_6':
            return subtask.sla_overdue_6_user_ids

        return self.env['res.users']

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

        # task-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_task_kanban_drag_access'
        ):
            return True

        # fallback to project-level access
        return bool(
            self.project_id and self.project_id._current_user_has_kanban_drag_access()
        )

    def _current_user_has_governance_access(self):
        self.ensure_one()

        if self._is_full_project_manager_access():
            return True

        # task-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_task_governance_access'
        ):
            return True

        # fallback to project-level access
        return bool(
            self.project_id and self.project_id._current_user_has_governance_access()
        )

    def _current_user_has_deadline_change_access(self):
        self.ensure_one()

        if self._is_full_project_manager_access():
            return True

        # task-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_task_deadline_access'
        ):
            return True

        # fallback to project-level access
        return bool(
            self.project_id and self.project_id._current_user_has_deadline_change_access()
        )

    def check_access_rule(self, operation):
        if operation in ('write', 'unlink'):
            for rec in self:
                # Admin / Program Manager / Project Manager
                if rec._is_full_project_manager_access():
                    continue

                # Allow assigned approver only for approval button flow
                if (
                        operation == 'write'
                        and self.env.context.get('from_task_approval')
                        and rec._is_current_user_task_approver()
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
        'project_task_access_user_rel',
        'task_id',
        'user_id',
        string="Access Users",
        compute='_compute_access_user_ids',
        store=True,
    )

    @api.depends(
        'message_partner_ids',
        'user_ids',
        'subtask_ids.message_partner_ids',
        'subtask_ids.assignee_id',
        'project_id.access_user_ids'
    )
    def _compute_access_user_ids(self):
        for rec in self:
            users = self.env['res.users']
            users |= rec.message_partner_ids.mapped('user_ids')
            users |= rec.user_ids
            users |= rec.subtask_ids.mapped('message_partner_ids.user_ids')
            users |= rec.subtask_ids.mapped('assignee_id')
            if rec.project_id:
                users |= rec.project_id.access_user_ids
            rec.access_user_ids = [(6, 0, users.ids)]


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    progress = fields.Float("Stage Progress %")

    count_in_progress = fields.Boolean(
        string="Count In Progress",
        default=True,
        help="If unchecked, this stage will not be counted in task progress (example: Cancelled)."
    )
    @api.onchange('progress', 'count_in_progress')
    def _onchange_progress(self):
        for rec in self:
            # Workflow stages
            if rec.count_in_progress:
                if rec.progress < 0 or rec.progress > 100:
                    raise ValidationError(
                        "Workflow stage progress must be between 0 and 100."
                    )
            # Non-workflow stages (Cancelled)
            else:
                if rec.progress != 0:
                    raise ValidationError(
                        "Non-progress stages must have exactly 0 progress."
                    )

    @api.constrains('progress', 'project_ids', 'count_in_progress')
    def _check_total_stage_progress(self):
        for rec in self:
            # 1️⃣ Individual validation
            if rec.count_in_progress:
                if rec.progress < 0 or rec.progress > 100:
                    raise ValidationError(
                        "Workflow stage progress must be between 0 and 100."
                    )
            else:
                if rec.progress != 0:
                    raise ValidationError(
                        "Non-progress stages must have exactly 0 progress."
                    )

            # 2️⃣ Workflow total must not exceed 100
            if rec.project_ids:
                for project in rec.project_ids:
                    stages = self.search([
                        ('project_ids', 'in', project.id),
                        ('count_in_progress', '=', True)
                    ])
                    total = sum(stages.mapped('progress'))

                    if total > 100:
                        raise ValidationError(
                            f"Total workflow task stage progress for project '{project.display_name}' cannot exceed 100."
                        )
            else:
                stages = self.search([
                    ('project_ids', '=', False),
                    ('count_in_progress', '=', True)
                ])
                total = sum(stages.mapped('progress'))

                if total > 100:
                    raise ValidationError(
                        "Total workflow progress of global task stages cannot exceed 100."
                    )
#########################################
    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    @api.model
    def _cron_recompute_sla(self):
        tasks = self.search([
            ('planned_end_date', '!=', False),
            ('is_done', '=', False),
        ])
        tasks._compute_subtask_sla()




    @api.model
    def _cron_sla_email(self):

        domain = [
            ('is_done', '=', False),
            ('planned_end_date', '!=', False),
            ('sla_stage', 'in', ['amber', 'red', 'red_3', 'red_6']),
        ]

        batch_size = 200
        offset = 0

        template_map = {
            'amber': 'project_main_mgmt.email_template_sla_amber',
            'red': 'project_main_mgmt.email_template_sla_red',
            'red_3': 'project_main_mgmt.email_template_sla_red_3',
            'red_6': 'project_main_mgmt.email_template_sla_red_6',
        }

        while True:
            tasks = self.search(domain, limit=batch_size, offset=offset)
            if not tasks:
                break

            offset += batch_size

            for task in tasks:
                try:
                    stage = task.sla_stage

                    # ✅ prevent duplicate emails
                    if task.sla_last_notified_stage == stage:
                        continue

                    users = self._get_sla_users(task, stage)

                    partners = users.mapped('partner_id').filtered(lambda p: p.email)

                    if not partners:
                        _logger.warning(f"No email recipients for task {task.id}")
                        continue

                    template = self.env.ref(template_map.get(stage), raise_if_not_found=False)

                    if not template:
                        _logger.error(f"Missing template for stage {stage}")
                        continue

                    template.with_context(
                        email_to=",".join(partners.mapped('email'))
                    ).send_mail(task.id, force_send=True)

                    # mark notified
                    task.sla_last_notified_stage = stage
                    task.sla_last_notified_date = fields.Date.today()

                except Exception:
                    _logger.exception(f"SLA email failed for task {task.id}")

            def _get_sla_users(self, task, stage):

                if stage == 'amber':
                    return task.sla_amber_user_ids

                elif stage == 'red':
                    return task.sla_red_user_ids

                elif stage == 'red_3':
                    return task.sla_overdue_3_user_ids

                elif stage == 'red_6':
                    return task.sla_overdue_6_user_ids

                return self.env['res.users']