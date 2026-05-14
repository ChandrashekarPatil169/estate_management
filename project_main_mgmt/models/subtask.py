from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class ProjectSubtask(models.Model):
    _name = 'project.subtask'
    _description = 'Subtask'
    _inherit = ['scheduler.mixin', 'mail.thread', 'mail.activity.mixin', 'hierarchy.sequence.mixin']

    name = fields.Char(string="Task Name", required=True)
    # project_id = fields.Many2one('project.project', required=True)
    story_id = fields.Many2one('project.user.story')
    assignee_id = fields.Many2one(
        'res.users',
        required=True,
        tracking=True
    )




    subtask_weightage = fields.Selection(
        [(str(i), str(i)) for i in range(1, 11)],
        string="Subtask Weightage",
        default='1'
    )

    # for approval reminder cron job
    last_review_reminder_date = fields.Date(copy=False)

    # code = fields.Char(readonly=True)
    # sequence_no = fields.Integer(readonly=True)
    estimate = fields.Float()
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
    # task_id = fields.Many2one('project.task', string="Parent Task")
    task_id = fields.Many2one(
        'project.task',
        string="Parent Task",
        required=True,
        ondelete='cascade',
        index=True
    )

    project_id = fields.Many2one(
        'project.project',
        required=True,
        readonly=True
    )

    sequence_no = fields.Integer(readonly=True, index=True)
    code = fields.Char(readonly=True)
    priorities = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="Priority", default='low')

    expected_end_date = fields.Date(string="Expected End Date", readonly=True)
    # In models/subtask.py

    # document_count = fields.Integer(compute='_compute_document_count')
    ##################################################
    # 🔥 PARENT SUBTASK
    parent_id = fields.Many2one(
        'project.subtask',
        string="Parent Subtask",
        ondelete='cascade',
        index=True
    )

    # 🔥 CHILD SUBTASKS
    child_ids = fields.One2many(
        'project.subtask',
        'parent_id',
        string="Subtasks"
    )

    task_label_id = fields.Many2one(
        'project.task.label.master',
        task_label_id=fields.Many2one(
            string="Subtask Label",
            domain="[('applies_to','=','subtask')]"
        ))
    #####################################################
    # -------------------------
    # GOVERNANCE (BOOLEAN ONLY)
    # -------------------------
    # Users who ARE ALLOWED to approve
    approver_ids = fields.Many2many(
        'res.users',
        string="Approvers",
        tracking=True
    )

    # User who ACTUALLY approved
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
        string="Evidence Required",
        # tracking=True
    )
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
    _sql_constraints = [
        (
            'subtask_sequence_unique_per_task',
            'unique(task_id, sequence_no)',
            'Subtask sequence must be unique per task.'
        )
    ]
    inherited_notes = fields.Html(
        string="Inherited Notes",
        compute="_compute_inherited_notes",
        sanitize=False
    )
    planned_start_date = fields.Date(string="Planned Start Date")
    planned_end_date = fields.Date(string="Planned End Date")
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
        copy=False
    )

    tag_ids = fields.Many2many(
        'project.tags',
        'project_subtask_project_tag_rel',
        'subtask_id',
        'tag_id',
        string="Tags",
        tracking=True
    )

    sla_stage = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red'),
            ('red_3', 'Overdue +3 Days'),
            ('red_6', 'Overdue +6 Days'),
        ],
        string="SLA Stage",
        compute="_compute_subtask_sla_stage",
        store=True,
        group_expand='_group_expand_sla_stage'
    )

    allow_timesheet_user_ids = fields.Many2many(
        'res.users',
        'project_subtask_timesheet_user_rel',  # 👈 different table from task
        'subtask_id',
        'user_id',
        string="Allowed Timesheet Users"
    )

    def _get_parent_field(self):
        return 'task_id'

    @api.model
    def _group_expand_sla_stage(self, stages, domain):
        return ['green', 'amber', 'red', 'red_3', 'red_6']

    @api.depends('planned_end_date', 'status')
    def _compute_subtask_sla_stage(self):
        today = fields.Date.today()

        for sub in self:

            if sub.status == 'done' or not sub.planned_end_date:
                sub.sla_stage = 'green'
                continue

            delta_days = (sub.planned_end_date - today).days

            if delta_days > 3:
                sub.sla_stage = 'green'

            elif 0 < delta_days <= 3:
                sub.sla_stage = 'amber'

            elif 0 >= delta_days > -3:
                sub.sla_stage = 'red'

            elif -3 >= delta_days > -6:
                sub.sla_stage = 'red_3'

            else:
                sub.sla_stage = 'red_6'

    def _compute_document_ids(self):
        for record in self:
            record.document_ids = self.env['ir.attachment'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])

    def _inverse_document_ids(self):
        for record in self:
            for attachment in record.document_ids:
                if not attachment.res_model or not attachment.res_id:
                    attachment.write({
                        'res_model': self._name,
                        'res_id': record.id
                    })

    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])

    # 3. Document Smart Button Action (Note: 'list' instead of 'tree')
    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Epic Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
            'target': 'current',
        }

    def _is_current_user_subtask_approver(self):
        self.ensure_one()
        return self.env.user in self.approver_ids

    def action_mark_done(self):
        self.ensure_one()

        # # 🛑 GOVERNANCE BLOCK: Check if the parent project is approved
        # if self.project_id.state != 'approved':
        #     raise UserError((
        #         "Governance Blocked: You cannot complete subtasks until the project '%s' is Approved."
        #     ) % self.project_id.name)

        if self.is_done:
            return

        if self.env.user not in self.approver_ids:
            raise UserError("You are not authorized to approve this subtask.")

        if self.evidence_required:
            attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
            ])

        # last_stage = self.env['project.subtask.stage'].search(
        #     [('name', 'not ilike', 'cancel')],
        #     order='sequence desc',
        #     limit=1
        # )

        # Find the stage where cumulative progress reaches 100
        done_stage = False
        total_progress = 0

        stages = self.env['project.subtask.stage'].search(
            [('name', 'not ilike', 'cancel')],
            order='sequence asc'
        )

        for stage in stages:
            total_progress += stage.progress or 0
            if total_progress >= 100:
                done_stage = stage
                break

        # 5️⃣ Final restricted approval flow
        self.with_context(
            skip_subtask_readonly_check=True,
            skip_subtask_kanban_check=True,
            skip_subtask_governance_check=True,
            skip_deadline_access_check=True,
            skip_subtask_stage_progress_check=True,
            from_subtask_approval=True,
        ).write({
            'is_done': True,
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
            'stage_id': done_stage.id if done_stage else self.stage_id.id,
            'status': 'done',
            'kanban_state': 'done'
        })

        # 🔥 force SLA recompute
        self._compute_subtask_sla_stage()

    @api.onchange('task_id')
    def _onchange_task_id(self):
        if self.task_id:
            self.project_id = self.task_id.project_id
            self.story_id = self.task_id.story_id

    ####################################subtask assigment mail######################

    # def _send_assignment_notification(self):
    #     template = self.env.ref('project_main_mgmt.email_template_subtask_assignment')
    #
    #     for subtask in self:
    #         if not subtask.assignee_id or not subtask.assignee_id.email:
    #             continue
    #
    #         template.send_mail(
    #             subtask.id,
    #             email_values={
    #                 'email_to': subtask.assignee_id.email,
    #             }
    #         )

    def _send_assignment_notification(self):
        template = self.env.ref(
            'project_main_mgmt.email_template_subtask_assignment',
            raise_if_not_found=False
        )

        if not template:
            return

        for subtask in self:
            user = subtask.assignee_id
            partner = user.partner_id if user else False

            if not partner or not partner.email:
                _logger.warning(f"Skipping subtask {subtask.id} - no email")
                continue

            mail_server = self.env['ir.mail_server'].search([], limit=1)

            smtp_user = mail_server.smtp_user if mail_server else None

            template.sudo().send_mail(
                subtask.id,
                force_send=True,
                email_values={
                    'email_to': partner.email,
                    'email_from': smtp_user,  # 🔥 CRITICAL FIX
                }
            )
            # subtask.message_post(
            #     body=f"""
            #         <b>Assignment Notification</b><br/>
            #         Subtask <b>{subtask.name}</b> assigned to <b>{subtask.assignee_id.name}</b>.
            #     """,
            #     partner_ids=[subtask.assignee_id.partner_id.id] if subtask.assignee_id.partner_id else [],
            # )

    #####################################################################################

    @api.model_create_multi
    def create(self, vals_list):

        if not self.env.user.has_group('base.group_system'):
            for vals in vals_list:
                project = False

                if vals.get('project_id'):
                    project = self.env['project.project'].browse(vals['project_id'])
                elif vals.get('task_id'):
                    task = self.env['project.task'].browse(vals['task_id'])
                    project = task.project_id

                if project:
                    if vals.get('approver_ids') and not project._current_user_has_governance_access():
                        raise AccessError(_("You do not have Governance access for this project."))

                    if (vals.get('planned_start_date') or vals.get('planned_end_date')) \
                            and not project._current_user_has_deadline_change_access():
                        raise AccessError(_("You do not have Changing Deadline access for this project."))

        for vals in vals_list:
            task_id = vals.get('task_id')
            parent_id = vals.get('parent_id')

            if parent_id and not task_id:
                parent = self.env['project.subtask'].browse(parent_id)
                task_id = parent.task_id.id

            if not task_id:
                raise ValidationError(_(
                    "Subtask must be created only from Task.\n\n"
                    "Valid flow:\n"
                    "Toggle ON  → Project → Product Backlog → Epic → User Story → Task → Subtask\n"
                    "Toggle OFF → Project → User Story → Task → Subtask"
                ))

        for vals in vals_list:

            # 🔥 FORCE DEFAULT STAGE (CRITICAL FIX)

            # 🔹 Fix for Kanban quick create
            if not vals.get('parent_id') and self.env.context.get('default_parent_id'):
                vals['parent_id'] = self.env.context['default_parent_id']

            if not vals.get('task_id') and self.env.context.get('default_task_id'):
                vals['task_id'] = self.env.context['default_task_id']

            if not vals.get('project_id') and self.env.context.get('default_project_id'):
                vals['project_id'] = self.env.context['default_project_id']

            parent_id = vals.get('parent_id')

            # 🔥 Creating under another subtask
            if parent_id:
                parent = self.env['project.subtask'].browse(parent_id)

                # inherit task
                if not vals.get('task_id') and parent.task_id:
                    vals['task_id'] = parent.task_id.id

                # inherit project
                if not vals.get('project_id') and parent.project_id:
                    vals['project_id'] = parent.project_id.id

                if not vals.get('story_id') and parent.story_id:
                    vals['story_id'] = parent.story_id.id

                # 🔥 Generate hierarchical sequence
                seq = self._next_sequence([('parent_id', '=', parent.id)])
                vals['sequence_no'] = seq
                vals['code'] = f"{parent.code}-ST{seq}"

            # 🔥 Creating directly under task
            elif vals.get('task_id'):
                task = self.env['project.task'].browse(vals['task_id'])

                if not vals.get('project_id') and task.project_id:
                    vals['project_id'] = task.project_id.id

                if not vals.get('story_id') and task.story_id:
                    vals['story_id'] = task.story_id.id

                seq = self._next_sequence([
                    ('task_id', '=', task.id),
                    ('parent_id', '=', False)
                ])
                vals['sequence_no'] = seq
                vals['code'] = f"{task.code}-ST{seq}"

            # 🔥 Prefix name
            if vals.get('code') and vals.get('name'):
                if not vals['name'].startswith(vals['code']):
                    vals['name'] = f"{vals['code']} - {vals['name']}"

        records = super().create(vals_list)

        # for rec in records:
        #     if rec.stage_id:
        #         rec.subtask_progress = rec.stage_id.progress
        for rec in records:
            if rec.stage_id:
                if not rec.stage_id.count_in_progress:
                    rec.subtask_progress = 0
                else:
                    stages = self.env['project.subtask.stage'].search([
                        ('count_in_progress', '=', True),
                        ('sequence', '<=', rec.stage_id.sequence)
                    ], order='sequence')

                    rec.subtask_progress = min(sum(stages.mapped('progress')), 100)
        # 🔥 ADD THIS BLOCK HERE
        for subtask in records:
            if subtask.assignee_id:
                # subtask._send_assignment_notification()
                subtask.sudo()._send_assignment_notification()

        return records

    def write(self, vals):

        
        if self.env.context.get('skip_scheduler_chain'):
            return super(ProjectSubtask, self).write(vals)

        if self.env.context.get('from_subtask_timesheet_edit'):
            return super(ProjectSubtask, self).write(vals)

        if self.env.context.get('from_timer_create'):
            return super(ProjectSubtask, self).write(vals)

        self._check_subtask_readonly_access(vals)
        # 🔹 Sync kanban state BEFORE write
        if 'status' in vals:
            vals['kanban_state'] = vals['status']

            # Detect kanban drag-like write
        is_kanban_drag = any(k in vals for k in [
            'stage_id', 'status', 'kanban_state', 'state', 'sequence', 'date_last_stage_update'
        ])

        # Sync kanban state if you use status
        if 'status' in vals and 'kanban_state' in self._fields:
            vals['kanban_state'] = vals['status']

        # 🔥 Kanban drag permission
        if (
                not self.env.context.get('skip_subtask_kanban_check')
                and is_kanban_drag
        ):
            for rec in self:
                # allow approver only through approval button
                if (
                        self.env.context.get('from_subtask_approval')
                        and rec._is_current_user_subtask_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'stage_id', 'status', 'kanban_state'
                })
                ):
                    continue
                rec._check_project_follower_kanban_drag_access()

            # ✅ Governance access
            # ✅ Governance access
        if (
                not self.env.context.get('skip_subtask_governance_check')
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

                # allow assigned approver only for approval button flow
                if (
                        self.env.context.get('from_subtask_approval')
                        and rec._is_current_user_subtask_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'stage_id', 'status', 'kanban_state'
                })
                ):
                    continue

                if not rec._current_user_has_governance_access():
                    raise AccessError(_("You do not have Governance access for this subtask."))



            # 🔥 Deadline permission (skip internal auto writes)
        if 'planned_start_date' in vals or 'planned_end_date' in vals:
            if not (
                    self.env.context.get('from_kanban_drag_auto')
                    or self.env.context.get('skip_scheduler_chain')
                    or self.env.context.get('skip_deadline_access_check')
                    or (
                            is_kanban_drag and all(
                        rec.project_id and rec.project_id._current_user_has_kanban_drag_access()
                        for rec in self
                    )
                    )
            ):
                self._check_project_follower_deadline_access()

        # 🔥 capture BEFORE write
        approver_map = {}
        if 'approver_ids' in vals:
            for rec in self:
                approver_map[rec.id] = rec.approver_ids

        # 🔹 Sync kanban state BEFORE write
        # if 'status' in vals:
        #     vals['kanban_state'] = vals['status']

        # 🔥 Validate total = 100 only when moving to Done stage
        if 'stage_id' in vals:
            self._check_stage_progress_total_is_100(vals['stage_id'])

        # 🔥 Single super call
        res = super(ProjectSubtask, self).write(vals)

        # ---------- AFTER WRITE ----------
        if 'stage_id' in vals:
            stage_obj = self.env['project.subtask.stage']

            for rec in self:
                new_stage = rec.stage_id

                if not new_stage:
                    continue

                # 🔹 Cancel / non-progress stage → force 0
                if not new_stage.count_in_progress:
                    super(ProjectSubtask, rec).write({
                        'subtask_progress': 0
                    })
                    continue

                # 🔹 Fresh cumulative progress up to current stage
                stages = stage_obj.search([
                    ('count_in_progress', '=', True),
                    ('sequence', '<=', new_stage.sequence)
                ], order='sequence')

                progress_total = sum(stages.mapped('progress'))

                # 🔹 Safety cap
                progress_total = max(0, min(100, progress_total))

                # 🔥 Update progress safely
                super(ProjectSubtask, rec).write({
                    'subtask_progress': progress_total
                })

        # 🔥 Handle move to another task
        if 'task_id' in vals:
            for sub in self:
                if sub.task_id:
                    if sub.parent_id:
                        seq = sub._next_sequence([
                            ('parent_id', '=', sub.parent_id.id),
                        ])
                        code = f"{sub.parent_id.code}-ST{seq}"
                    else:
                        seq = sub._next_sequence([
                            ('task_id', '=', sub.task_id.id),
                            ('parent_id', '=', False),
                        ])
                        code = f"{sub.task_id.code}-ST{seq}"

                    super(ProjectSubtask, sub).write({
                        'sequence_no': seq,
                        'code': code,
                    })

        # 🔒 Preserve prefix on rename
        if 'name' in vals:
            for sub in self:
                if sub.code and sub.name and not sub.name.startswith(sub.code):
                    super(ProjectSubtask, sub).write({
                        'name': f"{sub.code} - {sub.name}"
                    })

        if 'planned_end_date' in vals or 'status' in vals:
            self._compute_subtask_sla_stage()

        # 🔥 HANDLE APPROVER CHANGE AFTER WRITE
        if 'approver_ids' in vals:
            self._handle_approver_change(vals, approver_map)
        print("SUBTASK WRITE VALS:", vals)
        print("SUBTASK WRITE CONTEXT:", self.env.context)

        return res

    def read(self, fields=None, load='_classic_read'):
        return super(ProjectSubtask, self.sudo()).read(fields, load=load)

    def _check_project_follower_kanban_drag_access(self):
        if self.env.user.has_group('base.group_system'):
            return

        for rec in self:
            project = rec.project_id
            if project and not project._current_user_has_kanban_drag_access():
                raise AccessError(_("You do not have Kanban Drag & Drop access for this project."))

    def _check_project_follower_governance_access(self):
        if self.env.user.has_group('base.group_system'):
            return
        for sub in self:
            project = sub.project_id
            if project and not project._current_user_has_governance_access():
                raise AccessError(_("You do not have Governance access for this project."))

    def _check_project_follower_deadline_access(self):
        if self.env.user.has_group('base.group_system'):
            return

        for rec in self:
            project = rec.project_id
            if not project:
                continue

            if not project._current_user_has_deadline_change_access():
                raise AccessError(_("You do not have Changing Deadline access for this project."))

    # def _is_project_user_readonly_mode(self):
    #     if self.env.user.has_group('base.group_system'):
    #         return False
    #     return self.env.user.has_group('project.group_project_user')
    def _is_project_user_readonly_mode(self):
        for rec in self:
            if rec._is_full_project_manager_access():
                return False
        return self.env.user.has_group('project.group_project_user')

    # def _check_subtask_readonly_access(self, vals):
    #     # approval flow skip
    #     if self.env.context.get('skip_subtask_readonly_check') or self.env.context.get('from_subtask_approval'):
    #         return
    #
    #     if not self._is_project_user_readonly_mode():
    #         return
    #
    #     # allow pure timesheet inline edits
    #     if 'timesheet_ids' in vals or 'account_analytic_line_ids' in vals or 'timesheet_line_ids' in vals:
    #         return
    #
    #     # timesheet_allowed = {'timesheet_ids', 'account_analytic_line_ids', 'timesheet_line_ids'}
    #     # if set(vals.keys()).issubset(timesheet_allowed):
    #     #     return
    #
    #     allowed_fields = {
    #
    #         # SLA auto-computed fields
    #         'sla_risk',
    #         'sla_state',
    #         'sla_stage',
    #         'sla_days_remaining',
    #         'sla_days_label',
    #         # chatter
    #         'message_follower_ids',
    #         'message_partner_ids',
    #         'message_ids',
    #         'message_main_attachment_id',
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
    #         # 🔥 ADD THESE TIMER FIELDS
    #         'timer_state',
    #         'timer_running',
    #         'task_start_date',
    #         'task_accumulated_time',
    #         'is_timer_running',
    #
    #     }
    #
    #     technical_ok = {
    #         'write_date',
    #         'write_uid',
    #         '__last_update',
    #         'display_name',
    #     }
    #
    #     forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
    #     if forbidden:
    #         print("SUBTASK BLOCKED FIELDS:", forbidden)
    #         raise AccessError(_("Subtask is read-only. You can only edit Timesheet lines and Chatter."))
    def _check_subtask_readonly_access(self, vals):
        # skip for internal flows
        if (
                self.env.context.get('skip_subtask_readonly_check')
                or self.env.context.get('from_subtask_approval')
                or self.env.context.get('from_subtask_timesheet_edit')
                or self.env.context.get('from_timer_create')
        ):
            return

        if not self._is_project_user_readonly_mode():
            return

        # allow pure timesheet inline edits
        if 'timesheet_ids' in vals or 'account_analytic_line_ids' in vals or 'timesheet_line_ids' in vals:
            return

        # allow harmless autosave fields from form while editing inline lines
        harmless_form_fields = {
            'priorities',
            'name',
            'tag_ids',
            'assignee_id',
            'write_date',
            'write_uid',
            '__last_update',
            'display_name',
        }
        if set(vals.keys()).issubset(harmless_form_fields):
            return

        allowed_fields = {
            # SLA auto-computed fields
            'sla_risk',
            'sla_state',
            'sla_stage',
            'sla_days_remaining',
            'sla_days_label',

            # chatter / followers
            'message_follower_ids',
            'message_partner_ids',
            'message_ids',
            'message_main_attachment_id',
            'activity_ids',
            'activity_state',
            'activity_exception_decoration',
            'activity_exception_icon',
            'activity_type_icon',
            'message_attachment_count',
            'message_has_error',
            'message_has_error_counter',
            'message_needaction',
            'message_needaction_counter',
            'message_has_sms_error',

            # timesheet
            'timesheet_ids',
            'timesheet_line_ids',
            'account_analytic_line_ids',

            # kanban / stage
            'stage_id',
            'status',
            'kanban_state',
            'state',
            'sequence',
            'date_last_stage_update',
            'priorities',

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

            # timer
            'task_start_date',
            'task_accumulated_time',
            'timer_state',
            'timer_running',
            'is_timer_running',
            'subtask_ids',
        }

        technical_ok = {
            'write_date',
            'write_uid',
            '__last_update',
            'display_name',
        }

        # forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
        # if forbidden:
        #     print("SUBTASK BLOCKED FIELDS:", forbidden)
        #     raise AccessError(_("Subtask is read-only. You can only edit Timesheet lines and Chatter."))

    def _check_stage_progress_total_is_100(self, new_stage_id):
        stage_obj = self.env['project.subtask.stage']
        new_stage = stage_obj.browse(new_stage_id)

        for rec in self:
            # Only validate when moving to Done / folded stage
            if not new_stage or not new_stage.fold:
                continue

            # Skip Cancel / non-progress stage
            if not new_stage.count_in_progress:
                continue

            # Get only workflow stages
            stages = stage_obj.search([
                ('count_in_progress', '=', True)
            ], order='sequence')

            total = sum(stages.mapped('progress'))

            if total != 100:
                raise ValidationError(
                    f"Total workflow subtask stage progress must be exactly 100 before moving to Done stage. "
                    f"Current total is {total}."
                )

    @api.constrains('name')
    def _check_code_prefix(self):
        for rec in self:
            if rec.code and rec.name and not rec.name.startswith(rec.code):
                raise ValidationError(
                    "System-generated subtask code cannot be removed."
                )

    @api.depends(
        'task_id.description',
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
            task = rec.task_id
            story = rec.story_id
            epic = story.epic_id if story else False
            backlog = epic.backlog_id if epic else False

            project = (
                story.project_id
                if story and story.project_id
                else (backlog.project_id if backlog and backlog.project_id else False)
            )

            task_note = task.description or "" if task else ""
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
                sections.append(f"<h4>User Story Notes</h4>{story_note}<hr/>")
            if task_note:
                sections.append(f"<h4>Task Notes</h4>{task_note}")

            rec.inherited_notes = "".join(sections)

    stage_id = fields.Many2one(
        'project.subtask.stage',
        string="Stage",
        default=lambda self: self._default_stage(),
        group_expand='_group_expand_stage',
        tracking=True
    )

    def _default_stage(self):

        return self.env['project.subtask.stage'].search([], order="sequence", limit=1)

    @api.model
    def _group_expand_stage(self, stages, domain):
        return self.env['project.subtask.stage'].search([], order='sequence')

    subtask_progress = fields.Float(
        string="Progress %",
        tracking=True
    )

    # def _create_timesheet_line(self, hours):
    #     self.env['account.analytic.line'].create({
    #         'project_id': self.project_id.id,
    #         'task_id': self.task_id.id,  # attach to parent task
    #         'employee_id': self.env.user.employee_id.id,
    #         'unit_amount': hours,
    #         'name': f"Subtask: {self.name}",
    #     })
    # timesheet_ids = fields.One2many(
    #     'account.analytic.line',
    #     'subtask_id',
    #     string='Timesheets'
    # )
    def _create_timesheet_line(self, hours):
        self.ensure_one()

        self.env['account.analytic.line'].with_context(from_timer_create=True).create({
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,
            'subtask_id': self.id,  # 🔥 VERY IMPORTANT
            'employee_id': self.env.user.employee_id.id,
            'unit_amount': hours,
            'name': f"Subtask: {self.name}",
        })

    subtask_count = fields.Integer(
        string="Subtasks",
        compute="_compute_subtask_count",
        store=True
    )

    @api.depends('child_ids')
    def _compute_subtask_count(self):

        for rec in self:
            rec.subtask_count = len(rec.child_ids)

    def action_view_child_subtasks(self):

        self.ensure_one()

        return {
            'name': f'Subtasks of {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'project.subtask',
            'view_mode': 'kanban,list,form',

            # 🔥 MOST IMPORTANT FILTER
            'domain': [('parent_id', '=', self.id)],

            'context': {
                'default_parent_id': self.id,
                'default_task_id': self.task_id.id,
                'default_project_id': self.project_id.id,
            },

            'target': 'current',
        }

    task_type_id = fields.Many2one(
        'project.task.type.master',
        task_type_id=fields.Many2one(
            string="Subtask Type",
            domain="[('applies_to','=','subtask')]"
        ))

    progress_color = fields.Char(
        string="Progress Color",
        compute="_compute_progress_color",
        store=False
    )

    @api.depends("subtask_progress")
    def _compute_progress_color(self):
        # get first config (assuming single master config)
        config = self.env['progress.config'].search([], limit=1)

        lines = config.line_ids.sorted(key=lambda l: l.min_value) if config else []

        for rec in self:
            color = 'bg-primary'  # fallback

            for line in lines:
                if line.min_value <= rec.subtask_progress <= line.max_value:
                    color = line.color
                    break

            rec.progress_color = color

    def _handle_approver_change(self, vals, approver_map):

        if 'approver_ids' not in vals:
            return

        for rec in self:
            old = approver_map.get(rec.id, self.env['res.users'])
            new = rec.approver_ids

            added = new - old
            removed = old - new

            if added:
                rec._notify_approver_added(added)

            if removed:
                rec._notify_approver_removed(removed)

    def _notify_approver_added(self, users):

        template = self.env.ref(
            'project_main_mgmt.email_template_approver_added',
            raise_if_not_found=False
        )

        if not template:
            _logger.error("Template not found: approver_added")
            return

            # ✅ Dynamic Sender: No more searching for 'Gmail SMTP' or hardcoded strings
        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )
        partners = users.mapped('partner_id').filtered(lambda p: p.email)

        if not partners:
            return

        for rec in self:  # ✅ REQUIRED LOOP
            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_from': email_from,
                    'recipient_ids': [(6, 0, partners.ids)],
                }
            )

    def _notify_approver_removed(self, users):

        template = self.env.ref(
            'project_main_mgmt.email_template_approver_removed',
            raise_if_not_found=False
        )

        if not template:
            _logger.error("Template not found: approver_removed")
            return

            # ✅ Dynamic Sender: No more searching for 'Gmail SMTP' or hardcoded strings
        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )


        partners = users.mapped('partner_id').filtered(lambda p: p.email)

        if not partners:
            return

        for rec in self:  # ✅ REQUIRED LOOP
            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_from': email_from,
                    'recipient_ids': [(6, 0, partners.ids)],
                }
            )

    tag_ids = fields.Many2many(
        'project.tags',
        'project_subtask_project_tag_rel',
        'subtask_id',
        'tag_id',
        string="Tags",
        tracking=True
    )

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

    sla_days_label = fields.Char(
        string="SLA Days",
        compute="_compute_sla_days_label",
        store=True,
    )

    sla_escalation_rules = fields.Text(
        string="SLA Escalation Rules"
    )

    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'subtask_sla_amber_rel',
        'subtask_id',
        'user_id',
        string="Amber Escalation Owners"
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'subtask_sla_red_rel',
        'subtask_id',
        'user_id',
        string="Red Escalation Owners"
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'subtask_sla_overdue3_rel',
        'subtask_id',
        'user_id',
        string="Overdue +3 Days Owners"
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'subtask_sla_overdue6_rel',
        'subtask_id',
        'user_id',
        string="Overdue +6 Days Owners"
    )

    @api.depends('planned_end_date', 'status', 'is_done')
    def _compute_subtask_sla(self):
        today = fields.Date.today()

        for sub in self:

            # Completed = Green
            if sub.is_done or sub.status == 'done':
                sub.sla_risk = 'green'
                sub.sla_state = 'green'
                sub.sla_stage = 'green'
                sub.sla_days_remaining = 0
                continue

            # No date = Green default
            if not sub.planned_end_date:
                sub.sla_risk = 'green'
                sub.sla_state = 'green'
                sub.sla_stage = 'green'
                sub.sla_days_remaining = 0
                continue

            delta_days = (sub.planned_end_date - today).days
            sub.sla_days_remaining = delta_days

            if delta_days > 3:
                sub.sla_risk = 'green'
                sub.sla_state = 'green'
                sub.sla_stage = 'green'


            elif 0 < delta_days <= 3:
                sub.sla_risk = 'amber'
                sub.sla_state = 'amber'
                sub.sla_stage = 'amber'


            elif 0 >= delta_days > -3:
                sub.sla_risk = 'red'
                sub.sla_state = 'red'
                sub.sla_stage = 'red'


            elif -3 >= delta_days > -6:
                sub.sla_risk = 'red'
                sub.sla_state = 'red'
                sub.sla_stage = 'red_3'


            else:
                sub.sla_risk = 'red'
                sub.sla_state = 'red'
                sub.sla_stage = 'red_6'

    @api.depends('sla_days_remaining', 'is_done', 'status')
    def _compute_sla_days_label(self):
        for sub in self:
            days = sub.sla_days_remaining

            if sub.is_done or sub.status == 'done':
                sub.sla_days_label = "Completed"
            elif days > 0:
                sub.sla_days_label = f"{days} days remaining"
            elif days == 0:
                sub.sla_days_label = "Due today"
            else:
                sub.sla_days_label = f"{abs(days)} days overdue"

    def action_open_child_subtask_sla_monitoring(self):
        self.ensure_one()

        kanban_view = self.env.ref('project_main_mgmt.view_subtask_sla_kanban')

        return {
            'type': 'ir.actions.act_window',
            'name': 'Subtask SLA Monitoring',
            'res_model': 'project.subtask',
            'views': [
                (kanban_view.id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': [
                ('parent_id', '=', self.id),
            ],
            'context': {
                'group_by': ['sla_stage'],
                'default_parent_id': self.id,
                'default_task_id': self.task_id.id,
                'default_project_id': self.project_id.id,
            },
        }

    def action_open_child_subtask_sla_7_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=7)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Child Subtasks - Next 7 Days',
            'res_model': 'project.subtask',
            'view_mode': 'list,form',
            'domain': [
                ('parent_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('status', '!=', 'done'),
            ],
            'context': {
                'default_parent_id': self.id,
                'default_task_id': self.task_id.id,
                'default_project_id': self.project_id.id,
            },
        }

    def action_open_child_subtask_sla_30_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=30)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Child Subtasks - Next 30 Days',
            'res_model': 'project.subtask',
            'view_mode': 'list,form',
            'domain': [
                ('parent_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('status', '!=', 'done'),
            ],
            'context': {
                'default_parent_id': self.id,
                'default_task_id': self.task_id.id,
                'default_project_id': self.project_id.id,
            },
        }
###############################################################
    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    @api.model
    def _cron_recompute_subtask_sla(self):
        subtasks = self.search([
            ('planned_end_date', '!=', False),
            ('is_done', '=', False),
        ])
        subtasks._compute_subtask_sla()

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

        # ✅ fetch once
        # ✅ Dynamic Sender: No more searching for 'Gmail SMTP' or hardcoded strings
        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )


        for sub in subtasks:
            try:
                stage = sub.sla_stage

                # ✅ skip duplicate notification
                if sub.sla_last_notified_stage == stage:
                    continue

                # ✅ get users
                users = self._get_subtask_sla_users(sub, stage)
                partners = users.mapped('partner_id').filtered(lambda p: p.email)

                if not partners:
                    _logger.warning(f"No recipients for subtask {sub.id}")
                    continue

                template_id = template_map.get(stage)
                template = self.env.ref(template_id, raise_if_not_found=False)

                if not template:
                    _logger.error(f"Missing template {template_id}")
                    continue

                # ✅ send mail
                template.send_mail(
                    sub.id,
                    force_send=True,
                    email_values={
                        'email_from': email_from,
                        'recipient_ids': [(6, 0, partners.ids)],
                    }
                )

                # ✅ mark notified
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

    def _is_full_project_manager_access(self):
        self.ensure_one()

        project = self.project_id or (self.task_id.project_id if self.task_id else False)

        if not project:
            return self.env.user.has_group('base.group_system')

        return project._is_full_project_manager_access()

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

        # subtask-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_subtask_kanban_drag_access'
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

        # subtask-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_subtask_governance_access'
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

        # subtask-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_subtask_deadline_access'
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
                        and self.env.context.get('from_subtask_approval')
                        and rec._is_current_user_subtask_approver()
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
        'project_subtask_access_user_rel',
        'subtask_id',
        'user_id',
        string="Access Users",
        compute='_compute_access_user_ids',
        store=True,
    )

    @api.depends(
        'message_partner_ids',
        'assignee_id',
        'task_id.access_user_ids',
        'project_id.access_user_ids'
    )
    def _compute_access_user_ids(self):
        for rec in self:
            users = self.env['res.users']
            users |= rec.message_partner_ids.mapped('user_ids')
            if rec.assignee_id:
                users |= rec.assignee_id
            if rec.task_id:
                users |= rec.task_id.access_user_ids
            if rec.project_id:
                users |= rec.project_id.access_user_ids
            rec.access_user_ids = [(6, 0, users.ids)]

    def write(self, vals):

        if self.env.context.get('skip_scheduler_chain'):
            return super(ProjectSubtask, self).write(vals)

        if self.env.context.get('from_subtask_timesheet_edit'):
            return super(ProjectSubtask, self).write(vals)

        if self.env.context.get('from_timer_create'):
            return super(ProjectSubtask, self).write(vals)

        self._check_subtask_readonly_access(vals)
        # 🔹 Sync kanban state BEFORE write
        if 'status' in vals:
            vals['kanban_state'] = vals['status']

            # Detect kanban drag-like write
        is_kanban_drag = any(k in vals for k in [
            'stage_id', 'status', 'kanban_state', 'state', 'sequence', 'date_last_stage_update'
        ])

        # Sync kanban state if you use status
        if 'status' in vals and 'kanban_state' in self._fields:
            vals['kanban_state'] = vals['status']

        # 🔥 Kanban drag permission
        if (
                not self.env.context.get('skip_subtask_kanban_check')
                and is_kanban_drag
        ):
            for rec in self:
                # allow approver only through approval button
                if (
                        self.env.context.get('from_subtask_approval')
                        and rec._is_current_user_subtask_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'stage_id', 'status', 'kanban_state'
                })
                ):
                    continue
                rec._check_project_follower_kanban_drag_access()

            # ✅ Governance access
            # ✅ Governance access
        if (
                not self.env.context.get('skip_subtask_governance_check')
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

                # allow assigned approver only for approval button flow
                if (
                        self.env.context.get('from_subtask_approval')
                        and rec._is_current_user_subtask_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'stage_id', 'status', 'kanban_state'
                })
                ):
                    continue

                if not rec._current_user_has_governance_access():
                    raise AccessError(_("You do not have Governance access for this subtask."))

            # 🔥 Deadline permission (skip internal auto writes)
        if 'planned_start_date' in vals or 'planned_end_date' in vals:
            if not (
                    self.env.context.get('from_kanban_drag_auto')
                    or self.env.context.get('skip_scheduler_chain')
                    or self.env.context.get('skip_deadline_access_check')
                    or (
                            is_kanban_drag and all(
                        rec.project_id and rec.project_id._current_user_has_kanban_drag_access()
                        for rec in self
                    )
                    )
            ):
                self._check_project_follower_deadline_access()

        # 🔥 capture BEFORE write
        approver_map = {}
        if 'approver_ids' in vals:
            for rec in self:
                approver_map[rec.id] = rec.approver_ids

        # 🔹 Sync kanban state BEFORE write
        # if 'status' in vals:
        #     vals['kanban_state'] = vals['status']

        # 🔥 Validate total = 100 only when moving to Done stage
        if 'stage_id' in vals:
            self._check_stage_progress_total_is_100(vals['stage_id'])

        # 🔥 Single super call
        res = super(ProjectSubtask, self).write(vals)

        # ---------- AFTER WRITE ----------
        if 'stage_id' in vals:
            stage_obj = self.env['project.subtask.stage']

            for rec in self:
                new_stage = rec.stage_id

                if not new_stage:
                    continue

                # 🔹 Cancel / non-progress stage → force 0
                if not new_stage.count_in_progress:
                    super(ProjectSubtask, rec).write({
                        'subtask_progress': 0
                    })
                    continue

                # 🔹 Fresh cumulative progress up to current stage
                stages = stage_obj.search([
                    ('count_in_progress', '=', True),
                    ('sequence', '<=', new_stage.sequence)
                ], order='sequence')

                progress_total = sum(stages.mapped('progress'))

                # 🔹 Safety cap
                progress_total = max(0, min(100, progress_total))

                # 🔥 Update progress safely
                super(ProjectSubtask, rec).write({
                    'subtask_progress': progress_total
                })

        # 🔥 Handle move to another task
        if 'task_id' in vals:
            for sub in self:
                if sub.task_id:
                    if sub.parent_id:
                        seq = sub._next_sequence([
                            ('parent_id', '=', sub.parent_id.id),
                        ])
                        code = f"{sub.parent_id.code}-ST{seq}"
                    else:
                        seq = sub._next_sequence([
                            ('task_id', '=', sub.task_id.id),
                            ('parent_id', '=', False),
                        ])
                        code = f"{sub.task_id.code}-ST{seq}"

                    super(ProjectSubtask, sub).write({
                        'sequence_no': seq,
                        'code': code,
                    })

        # 🔒 Preserve prefix on rename
        if 'name' in vals:
            for sub in self:
                if sub.code and sub.name and not sub.name.startswith(sub.code):
                    super(ProjectSubtask, sub).write({
                        'name': f"{sub.code} - {sub.name}"
                    })

        if 'planned_end_date' in vals or 'status' in vals:
            self._compute_subtask_sla_stage()

        # 🔥 HANDLE APPROVER CHANGE AFTER WRITE
        if 'approver_ids' in vals:
            self._handle_approver_change(vals, approver_map)
        print("SUBTASK WRITE VALS:", vals)
        print("SUBTASK WRITE CONTEXT:", self.env.context)

        return res



class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model_create_multi
    def create(self, vals_list):
        user = self.env.user

        for vals in vals_list:

            # ✅ 1. FORCE EMPLOYEE IF MISSING
            if not vals.get('employee_id'):
                employee = user.employee_id

                # 🔥 fallback: pick ANY employee if not linked
                if not employee:
                    employee = self.env['hr.employee'].sudo().search([], limit=1)

                if employee:
                    vals['employee_id'] = employee.id

            # ✅ 2. FORCE COMPANY ALIGNMENT
            if vals.get('employee_id'):
                emp = self.env['hr.employee'].sudo().browse(vals['employee_id'])

                if emp and emp.company_id:
                    vals['company_id'] = emp.company_id.id

        # ✅ 3. BYPASS VALIDATION USING CONTEXT
        return super(
            AccountAnalyticLine,
            self.with_context(
                bypass_timesheet_company_check=True,
                allowed_company_ids=self.env.user.company_ids.ids
            )
        ).create(vals_list)


class ProjectSubtaskStage(models.Model):
    _name = 'project.subtask.stage'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean()
    progress = fields.Float(string="Progress %")  # 🔥 ADD THIS

    count_in_progress = fields.Boolean(
        string="Count in Progress",
        default=True,
        help="If unchecked, this stage will not be counted in subtask progress calculation (example: Cancelled)."
    )

    # @api.onchange('progress', 'count_in_progress')
    # def _onchange_progress(self):
    #     for rec in self:
    #         # allow kanban quick create with 0
    #         if rec.progress < 0 or rec.progress > 100:
    #             raise ValidationError(
    #                 "Each subtask stage progress must be between 0 and 100 only."
    #             )
    #
    #         # Cancel / non-progress stage must be 0
    #         if not rec.count_in_progress and rec.progress != 0:
    #             rec.progress = 0
    @api.onchange('progress', 'count_in_progress')
    def _onchange_progress(self):
        for rec in self:
            # Non-workflow stage always 0
            if not rec.count_in_progress:
                rec.progress = 0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': 'This stage is excluded from workflow, so progress is reset to 0.'
                    }
                }

            # Invalid range -> reset to 0 and show popup
            if rec.progress < 0 or rec.progress > 100:
                rec.progress = 0
                return {
                    'warning': {
                        'title': 'Invalid Progress',
                        'message': 'Each subtask stage progress must be between 0 and 100 only. Progress has been reset to 0.'
                    }
                }

    @api.constrains('progress', 'count_in_progress')
    def _check_stage_progress(self):
        stages = self.search([])

        for rec in self:
            # 1️⃣ Each stage must be 0–100
            if rec.progress < 0 or rec.progress > 100:
                raise ValidationError(
                    "Each subtask stage progress must be between 0 and 100 only."
                )

            # 2️⃣ Non-workflow stage must be 0
            if not rec.count_in_progress and rec.progress != 0:
                raise ValidationError(
                    f"Stage '{rec.name}' is excluded from workflow, so progress must be 0."
                )

        # 3️⃣ Total of workflow stages cannot exceed 100
        workflow_stages = stages.filtered(lambda s: s.count_in_progress)
        total = sum(workflow_stages.mapped('progress'))

        if total > 100:
            raise ValidationError(
                f"Total workflow subtask stage progress cannot exceed 100. Current total is {total}."
            )
