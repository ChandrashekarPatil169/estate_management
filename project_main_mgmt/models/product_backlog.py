from odoo import models, fields, api,_
from datetime import timedelta
from odoo.exceptions import ValidationError, UserError,AccessError
import logging


_logger = logging.getLogger(__name__)

class ProductBacklog(models.Model):
    _name = 'product.backlog'
    _description = 'Product Backlog'
    _inherit = ['scheduler.mixin','mail.thread', 'mail.activity.mixin','hierarchy.sequence.mixin']

    name = fields.Char(string="Backlog Name", required=True, tracking=True)

    project_id = fields.Many2one('project.project', required=True, tracking=True)
    owner_id = fields.Many2one('res.users', string="Backlog Owner")
    ######################################
    code = fields.Char(readonly=True)
    sequence_no = fields.Integer(readonly=True)
##########################################################
    backlog_type_id = fields.Many2one(
        'product.backlog.type',
        string="Backlog Type",
        tracking=True,
        ondelete='restrict'
    )
    subproject_id = fields.Many2one('project.project')
    estimate = fields.Float(string="Work Hours (Hours)")
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

    description = fields.Text(string="Description / Notes")

    epic_ids = fields.One2many('project.epic', 'backlog_id')
    epic_count = fields.Integer(compute='_compute_epic_count', store=True)
    expected_end_date = fields.Date(string="Expected End Date", readonly=True)

    ####################
    planned_start_date = fields.Date(string="Planned Start Date")
    planned_end_date = fields.Date(string="Planned End Date")
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
        copy=False
    )
    # 1. Field to upload/view documents directly on the form
    document_ids = fields.Many2many(
        'ir.attachment',
        compute='_compute_document_ids',
        inverse='_inverse_document_ids',
        string="Documents"
    )

    # 2. Compute field to show the number of attachments on the smart button
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
        readonly=False,
        tracking=True
    )

    evidence_required = fields.Html(
        string="Evidence Required",
        # tracking=True
    )

    description = fields.Html("Backlog Notes")

    inherited_notes = fields.Html(
        string="Inherited Notes",
        compute="_compute_inherited_notes",
        sanitize=False
    )

    assignee_id = fields.Many2one(
        'res.users',
        # required=True,
        tracking=True
    )
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="Priority", default='low')

    # =========================
    # SLA (Derived from Epics)
    # =========================

    sla_risk = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_epic_sla",
        store=True,
    )

    sla_escalation_rules = fields.Text(string="SLA Escalation Rules")

    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'backlog_sla_amber_rel',
        'backlog_id',
        'user_id',
        string="Amber Escalation Owners"
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'backlog_sla_red_rel',
        'backlog_id',
        'user_id',
        string="Red Escalation Owners"
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'backlog_sla_overdue3_rel',
        'backlog_id',
        'user_id',
        string="Overdue +3 Days Owners"
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'backlog_sla_overdue6_rel',
        'backlog_id',
        'user_id',
        string="Overdue +6 Days Owners"
    )

    sla_state = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_epic_sla",
        store=True,
    )

    sla_days_remaining = fields.Integer(
        compute="_compute_epic_sla",
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
        compute="_compute_epic_sla",
        store=True,
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
        return 'project_id'



    @api.depends('planned_end_date', 'is_done')
    def _compute_epic_sla(self):
        today = fields.Date.today()

        for backlog_id in self:
            if backlog_id.is_done or not backlog_id.planned_end_date:
                backlog_id.sla_risk = 'green'
                backlog_id.sla_state = 'green'
                backlog_id.sla_stage = 'green'
                backlog_id.sla_days_remaining = 0
                continue

            delta_days = (backlog_id.planned_end_date - today).days
            backlog_id.sla_days_remaining = delta_days

            if delta_days > 3:
                backlog_id.sla_risk = 'green'
                backlog_id.sla_state = 'green'
                backlog_id.sla_stage = 'green'
            elif 0 < delta_days <= 3:
                backlog_id.sla_risk = 'amber'
                backlog_id.sla_state = 'amber'
                backlog_id.sla_stage = 'amber'
            elif 0 >= delta_days > -3:
                backlog_id.sla_risk = 'red'
                backlog_id.sla_state = 'red'
                backlog_id.sla_stage = 'red'
            elif -3 >= delta_days > -6:
                backlog_id.sla_risk = 'red'
                backlog_id.sla_state = 'red'
                backlog_id.sla_stage = 'red_3'
            else:
                backlog_id.sla_risk = 'red'
                backlog_id.sla_state = 'red'
                backlog_id.sla_stage = 'red_6'

    def action_open_story_sla_7_days(self):
        self.ensure_one()
        today = fields.Date.today()
        limit_date = today + timedelta(days=7)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Stories - Next 7 Days',
            'res_model': 'project.epic',
            'view_mode': 'list,form',
            'domain': [
                ('backlog_id', '=', self.id),
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
            'res_model': 'project.epic',
            'view_mode': 'list,form',
            'domain': [
                ('backlog_id', '=', self.id),
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
    #         'res_model': 'project.epic',
    #         'view_mode': 'kanban,list,form',
    #         'domain': [
    #             ('backlog_id', '=', self.id),
    #             ('is_done', '=', False),
    #         ],
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #     }
    #
    #

    def action_open_sla_monitoring(self):
        self.ensure_one()

        kanban_view = self.env.ref(
            'project_main_mgmt.view_epic_sla_kanban'
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': 'project.epic',
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view.id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': [
                ('backlog_id', '=', self.id),
                # ('is_done', '=', False),
            ],
            'context': {
                'group_by': ['sla_stage'],

            },
        }













    @api.model_create_multi
    def create(self, vals_list):

        if not self.env.user.has_group('base.group_system'):
            for vals in vals_list:
                project = False
                if vals.get('project_id'):
                    project = self.env['project.project'].browse(vals['project_id'])

                if project:
                    if vals.get('approver_ids') and not project._current_user_has_governance_access():
                        raise AccessError(_("You do not have Governance access for this project."))

                    if (vals.get('planned_start_date') or vals.get('planned_end_date')) \
                            and not project._current_user_has_deadline_change_access():
                        raise AccessError(_("You do not have Changing Deadline access for this project."))

        for vals in vals_list:
            project_id = vals.get('project_id') or self.env.context.get('default_project_id')

            if not project_id:
                raise ValidationError(_("Product Backlog must be created from Project."))

            project = self.env['project.project'].browse(project_id)

            if not project.enable_backlog_flow:
                raise ValidationError(_(
                    "Product Backlog cannot be created because 'Enable Backlog & Epic' is OFF.\n\n"
                    "Valid flow:\n"
                    "Project → User Story → Task → Subtask"
                ))


        records = super().create(vals_list)

        for rec in records:
            seq = rec._next_sequence([
                ('project_id', '=', rec.project_id.id),
            ])

            rec.sequence_no = seq
            rec.code = f"{rec.project_id.ref_code}-PB{seq}"

            if rec.name and not rec.name.startswith(rec.code):
                rec.name = f"{rec.code} - {rec.name}"
            # 🔥 run scheduler
            if rec.planned_end_date:
                rec._forward_chain()

        return records

    def write(self, vals):
        if self.env.context.get('skip_scheduler_chain'):
            return super(ProductBacklog, self).write(vals)
        self._check_backlog_readonly_access(vals)

        # if 'status' in vals or 'kanban_state' in vals:
        #     self._check_project_follower_kanban_drag_access()
        if (
                not self.env.context.get('skip_backlog_kanban_check')
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
                        self.env.context.get('from_backlog_approval')
                        and rec._is_current_user_backlog_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'status', 'kanban_state'
                })
                ):
                    continue
                rec._check_project_follower_kanban_drag_access()

            # ✅ Governance access check
        if (
                not self.env.context.get('skip_backlog_governance_check')
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
                        self.env.context.get('from_backlog_approval')
                        and rec._is_current_user_backlog_approver()
                        and set(vals.keys()).issubset({
                    'is_done', 'approved_by_id', 'completed_date', 'status', 'kanban_state'
                })
                ):
                    continue

                if not rec._current_user_has_governance_access():
                    raise AccessError(_("You do not have Governance access for this backlog."))


        is_kanban_drag = any(k in vals for k in [
            'stage_id', 'status', 'kanban_state', 'state', 'sequence', 'date_last_stage_update'
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

        result = super().write(vals)

        for record in self:
            changes = []
            for field_name in vals.keys():
                if field_name in record._fields:
                    field = record._fields[field_name]
                    value = record[field_name]

                    if field.type == 'many2one':
                        display_value = value.display_name if value else '-'
                    elif field.type in ['many2many', 'one2many']:
                        display_value = ", ".join(value.mapped('display_name')) if value else '-'
                    elif field.type == 'selection':
                        selection_dict = dict(field.selection)
                        display_value = selection_dict.get(value, value or '-')
                    elif field.type == 'boolean':
                        display_value = 'True' if value else 'False'
                    elif field.type == 'html':
                        display_value = 'Updated'
                    else:
                        display_value = value or '-'

                    changes.append(f"{field.string}: {display_value}")

            if changes:
                record.message_post(
                    body="Updated Fields:%s" % "".join(changes)
                )

        return result

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

    def _is_project_user_readonly_mode(self):
        for rec in self:
            if rec._is_full_project_manager_access():
                return False
            # Program Manager group + assigned as project.program_manager_id

        return self.env.user.has_group('project.group_project_user')

    def _check_backlog_readonly_access(self, vals):

        if self.env.context.get('skip_backlog_readonly_check'):
            return

        if not self._is_project_user_readonly_mode():
            return
        # for rec in self:
        #     if rec._is_full_project_manager_access():
        #         return

        allowed_fields = {
            # chatter
            'message_follower_ids',
            'message_partner_ids',
            'message_ids',
            'message_main_attachment_id',

            # governance
            'approver_ids',
            'approved_by_id',
            'is_done',
            'evidence_required',

            # deadlines
            'planned_start_date',
            'planned_end_date',
            'expected_end_date',
            'completed_date',

            # kanban
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
            raise AccessError(_("Product Backlog is read-only. You can only use Chatter."))

    def _is_full_project_manager_access(self):
        self.ensure_one()

        project = self.project_id
        if not project:
            return self.env.user.has_group('base.group_system')

        return project._is_full_project_manager_access()




    @api.depends('project_id.description')
    def _compute_inherited_notes(self):
        for rec in self:
            project_note = rec.project_id.description or ""

            rec.inherited_notes = f"""
            <h4>Project Notes</h4>
            {project_note}
            """




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

        # ✅ Governance rule: all epics must be done
        pending_epics = self.epic_ids.filtered(lambda e: not e.is_done)

        if pending_epics:
            raise ValidationError(
                "Backlog cannot be approved until ALL Epics are completed."
            )

        # Final approval
        self.with_context(
            skip_backlog_readonly_check=True,
            skip_backlog_kanban_check=True,
            skip_backlog_governance_check=True,
            skip_deadline_access_check=True,
            from_backlog_approval=True,
        ).write({
            'is_done': True,
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
            'status': 'done',
            'kanban_state': 'done',
        })

    def _compute_document_ids(self):
        for record in self:
            # Finds all attachments linked specifically to this record and model
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
            # Counts the number of linked attachments
            record.document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', record.id)
            ])

    # 3. Function called by the XML Smart Button
    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            # Change 'tree' to 'list' here
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id
            },
            'target': 'current',
        }

    ######################

    @api.depends('epic_ids')
    def _compute_epic_count(self):
        for rec in self:
            rec.epic_count = len(rec.epic_ids)

    # MOVED OUTSIDE: This must be aligned with the def above
    def action_view_backlog_epics(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Epics",
            "res_model": "project.epic",
            "view_mode": "list,kanban,form,timeline,activity,pivot",
            "domain": [("backlog_id", "=", self.id)],
            "context": {
                "default_backlog_id": self.id,
                "default_project_id": self.project_id.id,
            },
        }

    # backlog_progress = fields.Float(
    #     string="Product Backlog Progress %",
    #     compute="_compute_backlog_progress",
    #     store=True
    # )
    #
    # @api.depends('epic_ids.epic_progress')
    # def _compute_backlog_progress(self):
    #     for backlog in self:
    #         if backlog.epic_ids:
    #             total = sum(backlog.epic_ids.mapped('epic_progress'))
    #             backlog.backlog_progress = total / len(backlog.epic_ids)
    #         else:
    #             backlog.backlog_progress = 0.0

    backlog_progress = fields.Float(
        string="Backlog Progress %",
        compute="_compute_backlog_progress",
        store=True
    )

    @api.depends('epic_ids.epic_progress')
    def _compute_backlog_progress(self):
        for backlog in self:
            if backlog.epic_ids:
                vals = backlog.epic_ids.mapped('epic_progress')
                backlog.backlog_progress = sum(vals) / len(vals)
            else:
                backlog.backlog_progress = 0

    progress_color = fields.Char(
        string="Progress Color",
        compute="_compute_progress_color",
        store=False
    )

    @api.depends("backlog_progress")
    def _compute_progress_color(self):
        # get first config (assuming single master config)
        config = self.env['progress.config'].search([], limit=1)

        lines = config.line_ids.sorted(key=lambda l: l.min_value) if config else []

        for rec in self:
            color = 'bg-primary'  # fallback

            for line in lines:
                if line.min_value <= rec.backlog_progress <= line.max_value:
                    color = line.color
                    break

            rec.progress_color = color

##############################################################
    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    @api.model
    def _cron_recompute_backlog_sla(self):
        backlogs = self.search([
            ('planned_end_date', '!=', False),
            ('is_done', '=', False),
        ])
        backlogs._compute_epic_sla()

    @api.model
    def _cron_backlog_sla_email(self):

        domain = [
            ('is_done', '=', False),
            ('planned_end_date', '!=', False),
            ('sla_stage', 'in', ['amber', 'red', 'red_3', 'red_6']),
        ]

        batch_size = 200
        offset = 0

        template_map = {
            'amber': 'project_main_mgmt.email_template_backlog_sla_amber',
            'red': 'project_main_mgmt.email_template_backlog_sla_red',
            'red_3': 'project_main_mgmt.email_template_backlog_sla_red_3',
            'red_6': 'project_main_mgmt.email_template_backlog_sla_red_6',
        }

        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )


        while True:
            backlogs = self.search(domain, limit=batch_size, offset=offset)
            if not backlogs:
                break

            offset += batch_size

            for backlog in backlogs:
                try:
                    stage = backlog.sla_stage

                    # prevent duplicate
                    if backlog.sla_last_notified_stage == stage:
                        continue

                    users = self._get_sla_users(backlog, stage)

                    partners = users.mapped('partner_id').filtered(
                        lambda p: p.email
                    )

                    if not partners:
                        _logger.warning(f"No recipients for backlog {backlog.id}")
                        continue

                    template = self.env.ref(
                        template_map.get(stage),
                        raise_if_not_found=False
                    )

                    if not template:
                        _logger.error(f"Missing template for stage {stage}")
                        continue

                    template.send_mail(
                        backlog.id,
                        force_send=True,
                        email_values={
                            'email_from': email_from,
                            'recipient_ids': [(6, 0, partners.ids)],
                        }
                    )

                    backlog.sla_last_notified_stage = stage
                    backlog.sla_last_notified_date = fields.Date.today()

                except Exception:
                    _logger.exception(f"SLA email failed for backlog {backlog.id}")

    def _get_sla_users(self, backlog, stage):

        if stage == 'amber':
            return backlog.sla_amber_user_ids

        elif stage == 'red':
            return backlog.sla_red_user_ids

        elif stage == 'red_3':
            return backlog.sla_overdue_3_user_ids

        elif stage == 'red_6':
            return backlog.sla_overdue_6_user_ids

        return self.env['res.users']

    def _is_current_user_backlog_approver(self):
        self.ensure_one()
        return self.env.user in self.approver_ids

    def check_access_rule(self, operation):
        if operation in ('write', 'unlink'):
            for rec in self:
                # Admin / Program Manager / Project Manager
                if rec._is_full_project_manager_access():
                    continue

                # Allow assigned approver only for approval button flow
                if (
                        operation == 'write'
                        and self.env.context.get('from_backlog_approval')
                        and rec._is_current_user_backlog_approver()
                ):
                    continue

                # Allow kanban drag users for normal kanban updates
                if operation == 'write' and rec._current_user_has_kanban_drag_access():
                    continue

                break
            else:
                return

        return super().check_access_rule(operation)

    access_user_ids = fields.Many2many(
        'res.users',
        'product_backlog_access_user_rel',
        'backlog_id',
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


class ProductBacklogType(models.Model):


    _name = 'product.backlog.type'
    _description = 'Backlog Type'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
