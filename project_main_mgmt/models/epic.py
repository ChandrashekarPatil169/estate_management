from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError,AccessError
from datetime import timedelta
import logging
from odoo.orm.decorators import readonly

_logger = logging.getLogger(__name__)

class ProjectEpic(models.Model):
    _name = 'project.epic'
    _description = 'Epic'
    _inherit = ['scheduler.mixin','mail.thread', 'mail.activity.mixin', 'hierarchy.sequence.mixin']

    name = fields.Char(string="Epic Name", required=True, tracking=True)
    project_id = fields.Many2one('project.project', required=True)
    backlog_id = fields.Many2one('product.backlog')
    #########################
    code = fields.Char(readonly=True)
    sequence_no = fields.Integer(readonly=True)
    ##############################

    epic_status = fields.Selection([
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

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ])

    business_outcome = fields.Text()
    expected_value = fields.Char(string="Expected Value / Metric")
    target_milestone = fields.Many2one('project.milestone')
    estimated = fields.Float(string="Estimate")
    expected_end_date = fields.Date(string="Expected End Date", readonly=True)

    owner_id = fields.Many2one('res.users', string="Owner (PO)")

    approval_required = fields.Boolean()
    evidence_required = fields.Boolean()

    version_notes = fields.Text()

    user_story_ids = fields.One2many('project.user.story', 'epic_id')
    story_count = fields.Integer(compute='_compute_story_count', store=True)
    # 1. Collaborative Description Field
    # description = fields.Html(
    #     string="Description",
    #     sanitize_attributes=False,
    #     wrapper_tag='div'
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

    backlog_type_id = fields.Many2one(
        'product.backlog.type',
        string="Backlog Type",
        tracking=True,
        ondelete='restrict'
    )

    description = fields.Html("Epic Notes")

    inherited_notes = fields.Html(
        compute="_compute_inherited_notes",
        sanitize=False
    )
    assignee_id = fields.Many2one(
        'res.users',
        required=False,
        tracking=True
    )
    ######################

    # SLA Risk (derived)
    sla_risk = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_story_sla",
        store=True,
    )
    sla_escalation_rules = fields.Text(string="SLA Escalation Rules")

    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'epic_sla_amber_rel',
        'epic_id',
        'user_id',
        string="Amber Escalation Owners"
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'epic_sla_red_rel',
        'epic_id',
        'user_id',
        string="Red Escalation Owners"
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'epic_sla_overdue3_rel',
        'epic_id',
        'user_id',
        string="Overdue +3 Days Owners"
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'epic_sla_overdue6_rel',
        'epic_id',
        'user_id',
        string="Overdue +6 Days Owners"
    )

    sla_state = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_story_sla",
        store=True,
    )

    sla_days_remaining = fields.Integer(
        compute="_compute_story_sla",
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
        compute="_compute_story_sla",
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
        return 'backlog_id'

    @api.depends('planned_end_date', 'is_done')
    def _compute_story_sla(self):
        today = fields.Date.today()

        for epic in self:
            if  epic.is_done or not epic.planned_end_date:
                epic.sla_risk = 'green'
                epic.sla_state = 'green'
                epic.sla_stage = 'green'
                epic.sla_days_remaining = 0
                continue

            delta_days = (epic.planned_end_date - today).days
            epic.sla_days_remaining = delta_days

            if delta_days > 3:
                epic.sla_risk = 'green'
                epic.sla_state = 'green'
                epic.sla_stage = 'green'
            elif 0 < delta_days <= 3:
                epic.sla_risk = 'amber'
                epic.sla_state = 'amber'
                epic.sla_stage = 'amber'
            elif 0 >= delta_days > -3:
                epic.sla_risk = 'red'
                epic.sla_state = 'red'
                epic.sla_stage = 'red'
            elif -3 >= delta_days > -6:
                epic.sla_risk = 'red'
                epic.sla_state = 'red'
                epic.sla_stage = 'red_3'
            else:
                epic.sla_risk = 'red'
                epic.sla_state = 'red'
                epic.sla_stage = 'red_6'




    def action_open_story_sla_7_days(self):
            self.ensure_one()
            today = fields.Date.today()
            limit_date = today + timedelta(days=7)

            return {
                'type': 'ir.actions.act_window',
                'name': 'Upcoming Stories - Next 7 Days',
                'res_model': 'project.user.story',
                'view_mode': 'list,form',
                'domain': [
                    ('epic_id', '=', self.id),
                    ('planned_end_date', '>=', today),
                    ('planned_end_date', '<=', limit_date),
                    ('is_done', '=', False),
                ],
            }

    def action_open_story_sla_30_days(self):
        self.ensure_one()
        today = fields.Date.today()
        limit_date = today + timedelta(days=30)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Stories - Next 30 Days',
            'res_model': 'project.user.story',
            'view_mode': 'list,form',
            'domain': [
                ('epic_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
        }

    # def action_open_sla_monitoring(self):
    #     self.ensure_one()
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'SLA Monitoring',
    #         'res_model': 'project.user.story',
    #         'view_mode': 'kanban,list,form',
    #         'domain': [
    #             ('epic_id', '=', self.id),
    #             ('is_done', '=', False),
    #         ],
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #     }

    def action_open_sla_monitoring(self):
        self.ensure_one()

        kanban_view = self.env.ref(
            'project_main_mgmt.view_user_story_sla_kanban'
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': 'project.user.story',
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view.id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': [
                ('epic_id', '=', self.id),
                # ('is_done', '=', False),
            ],
            'context': {
                'group_by': ['sla_stage'],  # FIX HERE
            },
        }






    @api.model_create_multi
    def create(self, vals_list):

        if not self.env.user.has_group('base.group_system'):
            for vals in vals_list:
                project = False

                if vals.get('project_id'):
                    project = self.env['project.project'].browse(vals['project_id'])
                elif vals.get('backlog_id'):
                    backlog = self.env['product.backlog'].browse(vals['backlog_id'])
                    project = backlog.project_id

                if project:
                    if vals.get('approver_ids') and not project._current_user_has_governance_access():
                        raise AccessError(_("You do not have Governance access for this project."))

                    if (vals.get('planned_start_date') or vals.get('planned_end_date')) \
                            and not project._current_user_has_deadline_change_access():
                        raise AccessError(_("You do not have Changing Deadline access for this project."))
        for vals in vals_list:
            backlog_id = vals.get('backlog_id') or self.env.context.get('default_backlog_id')
            project_id = vals.get('project_id') or self.env.context.get('default_project_id')

            if backlog_id:
                backlog = self.env['product.backlog'].browse(backlog_id)
                project_id = project_id or backlog.project_id.id
            else:
                backlog = False

            if not project_id:
                raise ValidationError(_("Epic must be created from Product Backlog."))

            project = self.env['project.project'].browse(project_id)

            if not project.enable_backlog_flow:
                raise ValidationError(_(
                    "Epic cannot be created because 'Enable Backlog & Epic' is OFF.\n\n"
                    "Valid flow:\n"
                    "Project → User Story → Task → Subtask"
                ))

            if not backlog_id:
                raise ValidationError(_(
                    "Epic must be created only from Product Backlog.\n\n"
                    "Valid flow:\n"
                    "Project → Product Backlog → Epic → User Story → Task → Subtask"
                ))




        records = super().create(vals_list)

        for rec in records:
            # ✅ Correct receiver
            seq = rec._next_sequence([
                ('backlog_id', '=', rec.backlog_id.id),
            ])

            rec.sequence_no = seq
            rec.code = f"{rec.backlog_id.code}-E{seq}"

            # ✅ Prefix name ONCE
            if rec.name and not rec.name.startswith(rec.code):
                rec.name = f"{rec.code} - {rec.name}"

        return records

    def write(self, vals):

        if self.env.context.get('skip_scheduler_chain'):
            return super(ProjectEpic, self).write(vals)

        self._check_epic_readonly_access(vals)

        # 🔹 Sync colored dot with epic status
        if 'epic_status' in vals:
            vals['kanban_state'] = vals['epic_status']

        if (
                not self.env.context.get('skip_epic_kanban_check')
                and any(k in vals for k in [
            'epic_status',
            'kanban_state',
            'stage_id',
            'state',
            'sequence',
            'date_last_stage_update'
        ])
        ):
            for rec in self:
                # allow approver only through approval button flow
                if (
                        self.env.context.get('from_epic_approval')
                        and rec._is_current_user_epic_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'epic_status', 'kanban_state'
                })
                ):
                    continue
                rec._check_project_follower_kanban_drag_access()

            # ✅ Governance access
        if (
                not self.env.context.get('skip_epic_governance_check')
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
                        self.env.context.get('from_epic_approval')
                        and rec._is_current_user_epic_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'epic_status', 'kanban_state'
                })
                ):
                    continue

                if not rec._current_user_has_governance_access():
                    raise AccessError(_("You do not have Governance access for this epic."))

            # 🔥 Deadline access
        is_kanban_drag = any(k in vals for k in [
            'epic_status',
            'kanban_state',
            'stage_id',
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
                        rec.project_id and rec.project_id._current_user_has_kanban_drag_access()
                        for rec in self
                    )
                    )
            ):
                self._check_project_follower_deadline_access()
        return super().write(vals)

    def _check_project_follower_kanban_drag_access(self):

        for rec in self:
            # Admin / Program Manager / Project Manager -> full access
            if rec._is_full_project_manager_access():
                continue
            project = rec.project_id
            if project and not project._current_user_has_kanban_drag_access():
                raise AccessError(_("You do not have Kanban Drag & Drop access for this project."))

    def _check_project_follower_governance_access(self):

        for rec in self:
            # Admin / Program Manager / Project Manager -> full access
            if rec._is_full_project_manager_access():
                continue
            project = rec.project_id
            if project and not project._current_user_has_governance_access():
                raise AccessError(_("You do not have Governance access for this project."))

    def _check_project_follower_deadline_access(self):

        for rec in self:
            # Admin / Program Manager / Project Manager -> full access
            if rec._is_full_project_manager_access():
                continue
            project = rec.project_id
            if project and not project._current_user_has_deadline_change_access():
                raise AccessError(_("You do not have Changing Deadline access for this project."))

    def _is_full_project_manager_access(self):
        self.ensure_one()

        project = self.project_id
        if not project:
            return self.env.user.has_group('base.group_system')

        return project._is_full_project_manager_access()

    def _is_project_user_readonly_mode(self):
        for rec in self:
            if rec._is_full_project_manager_access():
                return False
        return self.env.user.has_group('project.group_project_user')

    def _check_epic_readonly_access(self, vals):

        if self.env.context.get('skip_epic_readonly_check'):
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
            'state',
            'kanban_state',
            'epic_status',
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
            raise AccessError(_("Epic is read-only. You can only use Chatter."))

    @api.depends(
        'backlog_id.description',
        'backlog_id.project_id.description'
    )
    def _compute_inherited_notes(self):
        for rec in self:
            project_note = rec.backlog_id.project_id.description or ""

            backlog_note = rec.backlog_id.description or ""

            rec.inherited_notes = f"""
            <h4>Project Notes</h4>{project_note}
            <hr/>
            <h4>Backlog Notes</h4>{backlog_note}
            """

    def _is_current_user_epic_approver(self):
        self.ensure_one()
        return self.env.user in self.approver_ids


    def action_mark_done(self):
        self.ensure_one()

        if self.is_done:
            return

        if not self.id:
            raise ValidationError("Please save the subtask before marking it done.")

        # ✅ ONLY selected approvers can approve
        if self.env.user not in self.approver_ids:
            raise UserError(
                "You are not authorized to approve this subtask."
            )

        # Evidence check
        if self.evidence_required:
            attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
            ])
            if not attachment_count:
                raise ValidationError(
                    "Evidence is required before completing this subtask."
                )


        # ✅ Governance rule: All stories must be done
        pending_stories = self.user_story_ids.filtered(lambda s: not s.is_done)

        if pending_stories:
            raise ValidationError(
                "Epic cannot be approved until ALL User Stories are completed."
            )

        # Final approval
        self.with_context(
            skip_epic_readonly_check=True,
            skip_epic_kanban_check=True,
            skip_epic_governance_check=True,
            skip_deadline_access_check=True,
            from_epic_approval=True,
        ).write({
            'is_done': True,
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
            'epic_status': 'done',
            'kanban_state': 'done',
        })

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
            'view_mode': 'kanban,list,form,',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
            'target': 'current',
        }

    @api.depends('user_story_ids')
    def _compute_story_count(self):
        for rec in self:
            rec.story_count = len(rec.user_story_ids)

    def action_view_epic_stories(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'User Stories',
            'res_model': 'project.user.story',

            # 🔥 VERY IMPORTANT → kanban must be first
            'view_mode': 'kanban,list,form,timeline',

            'domain': [('epic_id', '=', self.id)],
            'context': {
                'default_epic_id': self.id,
                'default_project_id': self.project_id.id,
                'default_backlog_id': self.backlog_id.id,
            },
        }

    # def action_view_epic_stories(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'User Stories',
    #         'res_model': 'project.user.story',
    #         'view_mode': 'list,form',
    #         'domain': [('epic_id', '=', self.id)],
    #         'context': {
    #             'default_epic_id': self.id,
    #             'default_project_id': self.project_id.id,
    #         },
    #     }

    epic_progress = fields.Float(
        string="Epic Progress %",
        compute="_compute_epic_progress",
        store=True
    )

    progress_color = fields.Char(
        string="Progress Color",
        compute="_compute_progress_color",
        store=False
    )

    @api.depends("epic_progress")
    def _compute_progress_color(self):
        # get first config (assuming single master config)
        config = self.env['progress.config'].search([], limit=1)

        lines = config.line_ids.sorted(key=lambda l: l.min_value) if config else []

        for rec in self:
            color = 'bg-primary'  # fallback

            for line in lines:
                if line.min_value <= rec.epic_progress <= line.max_value:
                    color = line.color
                    break

            rec.progress_color = color

    @api.depends('user_story_ids.task_avg_progress')
    def _compute_epic_progress(self):
        for epic in self:
            if epic.user_story_ids:
                vals = epic.user_story_ids.mapped('task_avg_progress')
                epic.epic_progress = sum(vals) / len(vals)
            else:
                epic.epic_progress = 0


#########################################################
    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    @api.model
    def _cron_recompute_epic_sla(self):
        epics = self.search([
            ('planned_end_date', '!=', False),
            ('is_done', '=', False),
        ])
        epics._compute_story_sla()

    @api.model
    def _cron_epic_sla_email(self):

        domain = [
            ('is_done', '=', False),
            ('planned_end_date', '!=', False),
            ('sla_stage', 'in', ['amber', 'red', 'red_3', 'red_6']),
        ]

        batch_size = 200
        offset = 0

        template_map = {
            'amber': 'project_main_mgmt.email_template_epic_sla_amber',
            'red': 'project_main_mgmt.email_template_epic_sla_red',
            'red_3': 'project_main_mgmt.email_template_epic_sla_red_3',
            'red_6': 'project_main_mgmt.email_template_epic_sla_red_6',
        }

        # ✅ Dynamic Sender: No more searching for 'Gmail SMTP' or hardcoded strings
        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )

        while True:
            epics = self.search(domain, limit=batch_size, offset=offset)
            if not epics:
                break

            offset += batch_size

            for epic in epics:
                try:
                    stage = epic.sla_stage

                    # prevent duplicate
                    if epic.sla_last_notified_stage == stage:
                        continue

                    users = self._get_sla_users(epic, stage)

                    partners = users.mapped('partner_id').filtered(
                        lambda p: p.email
                    )

                    if not partners:
                        _logger.warning(f"No recipients for epic {epic.id}")
                        continue

                    template = self.env.ref(
                        template_map.get(stage),
                        raise_if_not_found=False
                    )

                    if not template:
                        _logger.error(f"Missing template for stage {stage}")
                        continue

                    template.send_mail(
                        epic.id,
                        force_send=True,
                        email_values={
                            'email_from': email_from ,
                            'recipient_ids': [(6, 0, partners.ids)],
                        }
                    )

                    epic.sla_last_notified_stage = stage
                    epic.sla_last_notified_date = fields.Date.today()

                except Exception:
                    _logger.exception(f"SLA email failed for epic {epic.id}")

    def _get_sla_users(self, epic, stage):

        if stage == 'amber':
            return epic.sla_amber_user_ids

        elif stage == 'red':
            return epic.sla_red_user_ids

        elif stage == 'red_3':
            return epic.sla_overdue_3_user_ids

        elif stage == 'red_6':
            return epic.sla_overdue_6_user_ids

        return self.env['res.users']
###########################################
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

        # epic-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_epic_kanban_drag_access'
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

        # epic-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_epic_governance_access'
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

        # epic-level access
        if self._current_user_is_follower_with_subtype(
                'project_main_mgmt.mt_project_epic_deadline_access'
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
                        and self.env.context.get('from_epic_approval')
                        and rec._is_current_user_epic_approver()
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
        'project_epic_access_user_rel',
        'epic_id',
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
