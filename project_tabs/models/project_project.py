from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, UserError,AccessError


class ProjectProject(models.Model):
    _inherit = "project.project"

    # -----------------
    # Project charter approve
    # -----------------

    charter_state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)

    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)

    # UI Helper to show/hide buttons
    is_charter_approver = fields.Boolean(compute='_compute_is_charter_approver')

    @api.depends('charter_state')
    def _compute_is_charter_approver(self):
        # .sudo() allows regular users to 'peek' at the admin config
        # to see if they are on the list without throwing an Access Error.
        matrix = self.env['charter.approval.matrix'].sudo().search([('active', '=', True)], limit=1)
        approver_ids = matrix.line_ids.sudo().mapped('user_id').ids
        is_admin = self.env.user.has_group('base.group_system')

        for rec in self:
            rec.is_charter_approver = is_admin or (self.env.user.id in approver_ids)

    def action_submit_charter(self):
        for rec in self:
            # Check for purpose before submitting
            if not rec.project_purpose:
                raise UserError(_("Please complete Project Charter details before submitting."))

            # Allow move from draft OR rejected
            if rec.charter_state in ['draft', 'rejected']:
                rec.write({
                    'charter_state': 'pending',
                    'rejection_reason': False  # Clear reason for the new attempt
                })
                rec.message_post(body=_("Charter submitted for approval."))

    # def action_submit_charter(self):
    #         for rec in self:
    #             # Use your existing field 'project_purpose' check here
    #             rec.charter_state = 'pending'
    #

    def action_approve_charter(self):
        for rec in self:
            if not rec.is_charter_approver:
                raise UserError("You are not authorized to approve this charter.")
            rec.charter_state = 'approved'
    def action_reject_charter(self):
        self.ensure_one()
        if not self.is_charter_approver:
            raise AccessError(_("You are not authorized to reject this charter."))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Project Charter',
            'res_model': 'project.charter.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id}
        }

    # -------------------
    # Risk
    # -------------------

    risk_ids = fields.One2many(
        'project.risk',
        'project_id',
        string="Risks"
    )

    # =========================
    # Governance – Basic
    # =========================
    governance_profile_name = fields.Char(string="Governance Profile Name")

    governance_enabled = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="Governance Enabled",
        default='no'
    )

    governance_scope = fields.Selection([
        ('project', 'Project'),
        ('epic', 'Epic'),
        ('story', 'Story'),
        ('task', 'Task'),
    ], string="Governance Scope")

    governance_description = fields.Text(string="Governance Description / Notes")

    effective_from = fields.Date(string="Effective From Date")
    effective_until = fields.Date(string="Effective Until Date")

    # =========================
    # Quality Gates
    # =========================
    dor_required = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="Definition of Ready Required",
        default='no'
    )
    dor_text = fields.Text(string="Definition of Ready")

    evidence_mandatory = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="Evidence Mandatory",
        default='no'
    )

    evidence_types = fields.Selection([
        ('code', 'Code'),
        ('test', 'Test'),
        ('design', 'Design'),
        ('document', 'Document'),
    ], string="Evidence Types Required")

    dod_required = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string="Definition of Done",
        default='no'
    )

    acceptance_authority = fields.Selection([
        ('po', 'Product Owner'),
        ('qa', 'QA'),
        ('pm', 'Project Manager'),
    ], string="Acceptance Authority")

    # =========================
    # SLA & Escalation
    # =========================
    sla_applicable = fields.Boolean(string="SLA Applicable")
    sla_due_date_mandatory = fields.Boolean(string="SLA Due Date Mandatory")

    sla_priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="SLA Priority")

    sla_breach_allowed = fields.Boolean(string="SLA Breach Allowed")

    escalation_trigger = fields.Selection([
        ('sla', 'SLA Breach'),
        ('approval', 'Approval Delay'),
        ('blocked', 'Blocked Duration'),
    ], string="Escalation Trigger")

    escalation_delay = fields.Integer(string="Escalation Delay (Hours)")

    escalation_l1 = fields.Many2many(
        'res.users',
        'project_escalation_l1_rel',  # relation table name
        'project_id',  # column referring to current model
        'user_id',  # column referring to res.users
        string="Level-1 Escalation Owners"
    )

    escalation_l2 = fields.Many2many(
        'res.users',
        'project_escalation_l2_rel',
        'project_id',
        'user_id',
        string="Level-2 Escalation Owners"
    )

    escalation_l3 = fields.Many2many(
        'res.users',
        'project_escalation_l3_rel',
        'project_id',
        'user_id',
        string="Level-3 Escalation Owners"
    )

    # Leadership
    department_head_id = fields.Many2one(
        'hr.employee', string="Department Head/Director"
    )

    # Project Overview
    project_purpose = fields.Text(string="Purpose of Project")
    business_case = fields.Text(string="Business Case")
    project_goals_metrics = fields.Text(string="Goals / Metrics")
    expected_deliverables = fields.Text(string="Expected Deliverables")
    project_problems_issues = fields.Text(string="Problems / Issues")

    # Project Scope
    scope_in = fields.Text(string="In Scope")
    scope_out = fields.Text(string="Out of Scope")

    # Resources
    project_team_ids = fields.Many2many(
        'hr.employee',
        'project_project_team_rel',  # ✅ UNIQUE TABLE
        'project_id',
        'employee_id',
        string="Project Team"
    )

    support_resources = fields.Text(string="Support Team / Other Resources")
    special_needs = fields.Text(string="Special Needs")

    # Benefits & Customers
    process_owner_ids = fields.Many2many(
        'hr.employee',
        'project_process_owner_rel',  # ✅ UNIQUE TABLE
        'project_id',
        'employee_id',
        string="Process Owners"
    )

    key_stakeholder_ids = fields.Many2many(
        'hr.employee',
        'project_key_stakeholder_rel',  # ✅ UNIQUE TABLE
        'project_id',
        'employee_id',
        string="Key Stakeholders"
    )

    final_customer_id = fields.Many2one(
        'res.partner',
        string="Final Customer Contact"
    )

    expected_benefits = fields.Text(string="Expected Benefits")

    # Schedule
    milestone_count = fields.Integer(
        string="Milestones",
        compute="_compute_milestone_count"
    )


    # ADD THIS FIELD: It must match exactly what you are writing to in create()
    charter_approval_line_ids = fields.One2many(
        'charter.approval.matrix.line', # This should match your line model name
        'project_id',                   # This must exist in the line model
        string="Charter Approval Matrix"
    )

    def _compute_milestone_count(self):
        for project in self:
            project.milestone_count = self.env['project.milestone'].search_count([
                ('project_id', '=', project.id)
            ])

    def action_view_milestones(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Milestones',
            'res_model': 'project.milestone',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id
            },
        }

    # Risks / Constraints / Assumptions
    project_risks = fields.Text(string="Risks")
    project_constraints = fields.Text(string="Constraints")
    project_assumptions = fields.Text(string="Assumptions")

    # -------------------
    # calender & documents
    # -------------------

    calendar_event_count = fields.Integer(
        string="Meetings",
        compute="_compute_calendar_event_count"
    )

    document_count = fields.Integer(
        string="Documents",
        compute="_compute_document_count"
    )

    def _compute_calendar_event_count(self):
        Event = self.env['calendar.event']
        for project in self:
            project.calendar_event_count = Event.search_count([
                ('project_id', '=', project.id)
            ])

    def _compute_document_count(self):
        Attachment = self.env['ir.attachment']
        for project in self:
            project.document_count = Attachment.search_count([
                ('res_model', '=', 'project.project'),
                ('res_id', '=', project.id)
            ])

    def action_view_project_meetings(self):
        self.ensure_one()
        return {
            'name': 'Project Meetings',
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'calendar,list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
            }
        }

    def action_view_project_documents(self):
        self.ensure_one()
        return {
            'name': 'Project Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [
                ('res_model', '=', 'project.project'),
                ('res_id', '=', self.id)
            ],
            'context': {
                'default_res_model': 'project.project',
                'default_res_id': self.id,
            }
        }

    # --------------
    # Main Buttons
    # --------------

    backlog_count = fields.Integer(
        string="Product Backlog",
        compute="_compute_custom_counts"
    )

    epic_count = fields.Integer(
        string="Epic",
        compute="_compute_custom_counts"
    )

    user_story_count = fields.Integer(
        string="User Story",
        compute="_compute_custom_counts"
    )

    subtask_count = fields.Integer(
        string="Subtasks",
        compute="_compute_custom_counts"
    )

    def _compute_custom_counts(self):
        for rec in self:
            rec.backlog_count = self.env['product.backlog'].search_count([
                ('project_id', '=', rec.id)
            ])
            rec.epic_count = self.env['project.epic'].search_count([
                ('project_id', '=', rec.id)
            ])
            rec.user_story_count = self.env['project.user.story'].search_count([
                ('project_id', '=', rec.id)
            ])
            rec.subtask_count = self.env['project.subtask'].search_count([
                ('project_id', '=', rec.id)
            ])

    # Smart button actions
    def action_view_backlog(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Backlog',
            'res_model': 'product.backlog',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_epic(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Epics',
            'res_model': 'project.epic',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_user_story(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'User Stories',
            'res_model': 'project.user.story',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_subtask(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subtasks',
            'res_model': 'project.subtask',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    # @api.model_create_multi
    # def create(self, vals_list):
    #     projects = super().create(vals_list)
    #     # Your logic to pull from config
    #     config = self.env['charter.approval.matrix'].sudo().search([('active', '=', True)], limit=1)
    #     if config:
    #         for project in projects:
    #             lines = []
    #             for line in config.line_ids:
    #                 lines.append((0, 0, {
    #                     'user_id': line.user_id.id,
    #                     'sequence': line.sequence,
    #                     'status': 'pending',
    #                 }))
    #             # This call was failing because the field above was missing
    #             project.write({'charter_approval_line_ids': lines})
    #     return projects
