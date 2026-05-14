from odoo import models, fields, api, Command,_
from odoo.addons.project.models.project_project import STATUS_COLOR
from datetime import timedelta
from odoo.exceptions import ValidationError,UserError,AccessError
import logging


_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = ['project.project', 'scheduler.mixin']

    backlog_count = fields.Integer(
        string="Backlogs",
        compute="_compute_backlog_count"
    )
    expected_end_date = fields.Date(
        string="Expected End Date",
        tracking=True,
        readonly=True,
        help="The anticipated date for project completion based on agile planning."
    )
    last_update_status = fields.Selection([
        ('new', 'New'),
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold'),
        ('review', 'Review'),
        ('done', 'Complete'),
        ('cancelled', 'Cancelled'),
    ],
        string="Status",
        default='new',
        tracking=True,
        ondelete='set default'
    )



    sla_risk = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_backlog_sla",
        store=True,
    )

    sla_escalation_rules = fields.Text(string="SLA Escalation Rules")

    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'project_sla_amber_rel',
        'project_id',
        'user_id',
        string="Amber Escalation Owners"
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'project_sla_red_rel',
        'project_id',
        'user_id',
        string="Red Escalation Owners"
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'project_sla_overdue3_rel',
        'project_id',
        'user_id',
        string="Overdue +3 Days Owners"
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'project_sla_overdue6_rel',
        'project_id',
        'user_id',
        string="Overdue +6 Days Owners"
    )

    sla_state = fields.Selection(
        [('green', 'Green'), ('amber', 'Amber'), ('red', 'Red')],
        compute="_compute_backlog_sla",
        store=True,
    )

    sla_days_remaining = fields.Integer(
        compute="_compute_backlog_sla",
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
        compute="_compute_backlog_sla",
        store=True,
    )

    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="Priority", default='low')

    is_done = fields.Boolean(string="Is Completed", default=False)

    planned_start_date = fields.Date(string="Planned Start Date")
    planned_end_date = fields.Date(string="Planned End Date")
    completed_date = fields.Datetime(
        string="Completed Date",
        readonly=True,
        copy=False
    )
    estimate = fields.Float(string="Work Hours (Hours)")

    sla_days_label = fields.Char(
        string="SLA Days",
        compute="_compute_sla_days_label",
        store=True,
    )

    ####################################
    # Governance Approvers
    # project_approver_ids = fields.Many2many(
    #     'res.users',
    #     string="Project Approvers",
    #     tracking=True
    # )
    project_approver_ids = fields.Many2many(
        'res.users',
        'project_project_approver_rel',  # relation table name
        'project_id',  # this model column
        'user_id',  # comodel column
        string="Project Approvers",
        tracking=True
    )

    approved_by_id = fields.Many2one(
        'res.users',
        string="Approved By",
        readonly=True,
        tracking=True
    )

    is_project_done = fields.Boolean(
        string="Project Completed",
        readonly=True,
        tracking=True
    )

    evidence_required = fields.Html(
        string="Project Evidence Required"
    )
    access_user_ids = fields.Many2many(
        'res.users',
        'project_project_access_user_rel',
        'project_id',
        'user_id',
        string="Access Users",
        compute='_compute_access_user_ids',
        store=True,
    )
    timesheet_user_ids = fields.Many2many(
        'res.users',
        compute='_compute_timesheet_users',
        store=True
    )

    #######project manager email##############
    def _send_project_notification(self):
        template = self.env.ref('project_main_mgmt.email_template_project_notification')

        for project in self:
            if not project.user_id or not project.user_id.email:
                continue

            template.send_mail(
                project.id,
                email_values={
                    'email_to': project.user_id.email,
                }
            )

            # if project.user_id.partner_id:
            #     project.message_post(
            #         body=f"""
            #             <b>Project Notification</b><br/>
            #             Notification sent to <b>{project.user_id.name}</b>.
            #         """,
            #         partner_ids=[project.user_id.partner_id.id],
            #     )

    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.user_id:
                rec._send_project_notification()

        return records
#####################################################################

    def _check_all_work_items_done(self):
        """Validate that all required items are completed before project approval"""
        self.ensure_one()

        if self.enable_backlog_flow:

            records = self.env['product.backlog'].search([
                ('project_id', '=', self.id)
            ])

            label = "Product Backlogs"

        else:

            records = self.env['project.user.story'].search([
                '|',
                ('project_id', '=', self.id),
                ('epic_id.project_id', '=', self.id),
            ])

            label = "User Stories"

        if not records:
            raise ValidationError(
                f"No {label} exist for this project."
            )

        incomplete = records.filtered(lambda r: r.status != 'done')

        if incomplete:
            names = "\n".join(incomplete.mapped('name'))
            raise ValidationError(
                f"The following {label} are not completed:\n{names}"
            )

    def action_approve_project(self):
        self.ensure_one()

        if self.is_project_done:
            return

        # Approver validation
        if self.project_approver_ids and self.env.user not in self.project_approver_ids:
            raise UserError(
                "You are not authorized to approve this project."
            )

        # Work completion validation
        self._check_all_work_items_done()

        # Evidence validation
        if self.evidence_required:

            attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'project.project'),
                ('res_id', '=', self.id),
            ])

            if not attachment_count:
                raise ValidationError(
                    "Evidence is required before approving the project."
                )

        # Find Done stage
        done_stage = self.env['project.project.stage'].search([
            ('name', '=', 'Done')
        ], limit=1)

        if not done_stage:
            raise ValidationError("Done stage is not configured.")

        self.with_context(
            skip_project_readonly_check=True,
            skip_governance_check=True,
            skip_deadline_access_check=True,
            from_project_approval=True,
        ).write({
            'is_project_done': True,
            'approved_by_id': self.env.user.id,
            'completed_date': fields.Datetime.now(),
            'stage_id': done_stage.id,
        })

        # Final approval
        # self.write({
        #     'is_project_done': True,
        #     'approved_by_id': self.env.user.id,
        #     'completed_date': fields.Datetime.now(),
        #     'stage_id': done_stage.id,
        # })

    def write(self, vals):

        self._check_project_readonly_access(vals)

        # if any(k in vals for k in
        #        ['stage_id', 'status', 'state', 'kanban_state', 'sequence', 'date_last_stage_update']):
        #     self._check_project_kanban_drag_access()

        # 🔥 ADD HERE (Governance access check)
        if any(k in vals for k in [
            'project_approver_ids',
            'approved_by_id',
            'is_project_done',
            'evidence_required'
        ]):
            for rec in self:
                if rec._is_full_project_manager_access():
                    continue
                if (
                        self.env.context.get('from_project_approval')
                        and rec._is_current_user_project_approver()
                        and set(vals.keys()).issubset(
                    {'is_project_done', 'approved_by_id', 'completed_date', 'stage_id'})
                ):
                    continue
                if not rec._current_user_has_governance_access():
                    raise AccessError(_("You do not have Governance access for this project."))




        is_kanban_drag = any(k in vals for k in [
            'stage_id', 'status', 'state', 'kanban_state', 'sequence', 'date_last_stage_update'
        ])

        if 'planned_start_date' in vals or 'planned_end_date' in vals:
            if not (
                    self.env.context.get('from_kanban_drag_auto')
                    or self.env.context.get('skip_scheduler_chain')
                    or self.env.context.get('skip_deadline_access_check')
                    or (
                            is_kanban_drag and all(
                        rec._current_user_has_kanban_drag_access()
                        for rec in self
                    )
                    )
            ):
                self._check_project_deadline_change_access()

        if 'stage_id' in vals:

            done_stage = self.env['project.project.stage'].search([
                ('name', '=', 'Done')
            ], limit=1)

            if done_stage and vals['stage_id'] == done_stage.id:

                for project in self:
                    project._check_all_work_items_done()

        # ✅ Call super FIRST and store result
        res = super().write(vals)

        # ✅ AFTER write → trigger email
        if 'user_id' in vals:
            for project in self:
                project._send_project_notification()

        return res

    #######################################
    # ONE toggle for both Backlog + Epic
    enable_backlog_flow = fields.Boolean(
        string="Enable Backlog & Epic",
        default=False,  # ✅ enabled by default
    )

    # Toggle used by Kanban card
    def action_toggle_backlog_flow(self):
        for project in self:
            project.enable_backlog_flow = not project.enable_backlog_flow

    user_story_ids = fields.One2many(
        'project.user.story',
        'project_id',
        string="User Stories"
    )
    epic_ids = fields.One2many(
        'project.epic',
        'project_id',
        string="Epics"
    )

    task_ids = fields.One2many(
        'project.task',
        'project_id',
        string="Tasks"
    )

    subtask_ids = fields.One2many(
        'project.subtask',
        'project_id',
        string="Subtasks"
    )

    ##############################################################
    @api.depends('sla_days_remaining', 'is_project_done')
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
        return False

    @api.depends('planned_end_date', 'is_project_done')
    def _compute_backlog_sla(self):
        today = fields.Date.today()

        for project in self:
            if project.is_project_done or not project.planned_end_date:
                project.sla_risk = 'green'
                project.sla_state = 'green'
                project.sla_stage = 'green'
                project.sla_days_remaining = 0
                continue

            delta_days = (project.planned_end_date - today).days
            project.sla_days_remaining = delta_days

            if delta_days > 3:
                project.sla_risk = 'green'
                project.sla_state = 'green'
                project.sla_stage = 'green'
            elif 0 < delta_days <= 3:
                project.sla_risk = 'amber'
                project.sla_state = 'amber'
                project.sla_stage = 'amber'
            elif 0 >= delta_days > -3:
                project.sla_risk = 'red'
                project.sla_state = 'red'
                project.sla_stage = 'red'
            elif -3 >= delta_days > -6:
                project.sla_risk = 'red'
                project.sla_state = 'red'
                project.sla_stage = 'red_3'
            else:
                project.sla_risk = 'red'
                project.sla_state = 'red'
                project.sla_stage = 'red_6'

    # def action_open_story_sla_7_days(self):
    #     self.ensure_one()
    #     today = fields.Date.today()
    #     limit_date = today + timedelta(days=7)
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Upcoming Stories - Next 7 Days',
    #         'res_model': 'product.backlog',
    #         'view_mode': 'list,form',
    #         'domain': [
    #             ('project_id', '=', self.id),
    #             ('planned_end_date', '>=', today),
    #             ('planned_end_date', '<=', limit_date),
    #             ('is_done', '=', False),
    #         ],
    #     }
    #
    # def action_open_story_sla_30_days(self):
    #     self.ensure_one()
    #     today = fields.Date.today()
    #     limit_date = today + timedelta(days=30)
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Upcoming Stories - Next 30 Days',
    #         'res_model': 'product.backlog',
    #         'view_mode': 'list,form',
    #         'domain': [
    #             ('project_id', '=', self.id),
    #             ('planned_end_date', '>=', today),
    #             ('planned_end_date', '<=', limit_date),
    #             ('is_done', '=', False),
    #         ],
    #     }

    def _get_sla_story_model(self):
        """Return correct model based on backlog flow."""
        self.ensure_one()
        return 'product.backlog' if self.enable_backlog_flow else 'project.user.story'

    def action_open_story_sla_7_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=7)

        res_model = self._get_sla_story_model()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Stories - Next 7 Days',
            'res_model': res_model,
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
            'target': 'current',
        }

    def action_open_story_sla_30_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=30)

        res_model = self._get_sla_story_model()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Stories - Next 30 Days',
            'res_model': res_model,
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
            'target': 'current',
        }

    def action_open_sla_monitoring(self):
        self.ensure_one()

        if self.enable_backlog_flow:
            res_model = 'product.backlog'
            kanban_view = self.env.ref(
                'project_main_mgmt.view_product_backlog_sla_kanban'
            )
            domain = [
                ('project_id', '=', self.id),
                # ('is_done', '=', False),
            ]

        else:
            res_model = 'project.user.story'
            kanban_view = self.env.ref(
                'project_main_mgmt.view_user_story_sla_kanban'
            )
            domain = [
                ('project_id', '=', self.id),
                # ('is_done', '=', False),
            ]

        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': res_model,
            'view_mode': 'kanban,list,form',
            'views': [
                (kanban_view.id, 'kanban'),
                (False, 'list'),
                (False, 'form'),
            ],
            'domain': domain,
            'context': {
                'group_by': ['sla_stage'],
            },
            'target': 'current',
        }

    # def action_open_sla_monitoring(self):
    #     """
    #     Open SLA Monitoring view.
    #     - If Backlog flow is enabled → show Product Backlogs
    #     - If Backlog flow is disabled → show User Stories
    #     """
    #     self.ensure_one()
    #     kanban_view = self.env.ref(
    #         'project_main_mgmt.view_product_backlog_sla_kanban'
    #     )
    #
    #     if self.enable_backlog_flow:
    #         res_model = 'product.backlog'
    #         domain = [
    #             ('project_id', '=', self.id),
    #             ('is_done', '=', False),
    #         ]
    #     else:
    #         res_model = 'project.user.story'
    #         domain = [
    #             ('project_id', '=', self.id),
    #             ('is_done', '=', False),
    #         ]
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'SLA Monitoring',
    #         'res_model': res_model,
    #         'view_mode': 'kanban,list,form',
    #         'views': [
    #             (kanban_view.id, 'kanban'),
    #             (False, 'list'),
    #             (False, 'form'),
    #         ],
    #         'domain': domain,
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #         'target': 'current',
    #     }

    # def action_open_sla_monitoring(self):
    #     self.ensure_one()
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'SLA Monitoring',
    #         'res_model': 'product.backlog',
    #         'view_mode': 'kanban,list,form',
    #         'domain': [
    #             ('project_id', '=', self.id),
    #             ('is_done', '=', False),
    #         ],
    #         'context': {
    #             'group_by': 'sla_stage',
    #         },
    #     }

    def _compute_backlog_count(self):
        for rec in self:
            rec.backlog_count = self.env['product.backlog'].search_count([
                ('project_id', '=', rec.id)
            ])

    def action_view_product_backlogs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Backlogs',
            'res_model': 'product.backlog',
            'view_mode': 'kanban,list,form,timeline,activity,pivot',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id
            }
        }

    epic_count = fields.Integer(
        string="Epics",
        compute="_compute_epic_count"
    )

    def _compute_epic_count(self):
        for rec in self:
            rec.epic_count = self.env['project.epic'].search_count([
                ('project_id', '=', rec.id)
            ])

    def action_view_project_epics(self):
        self.ensure_one()

        backlog = self.env['product.backlog'].search(
            [('project_id', '=', self.id)],
            limit=1
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Epics',
            'res_model': 'project.epic',
            'view_mode': 'kanban,list,form,timeline,activity,pivot',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_backlog_id': backlog.id if backlog else False,
            }
        }

    subtask_count = fields.Integer(
        string="Subtasks",
        compute="_compute_subtask_count"
    )




    #######################################
    sprint_count = fields.Integer(
        string="Sprints",
        compute="_compute_sprint_count"
    )

    def _compute_sprint_count(self):
        for project in self:
            project.sprint_count = self.env['project.sprint'].search_count([
                ('project_id', '=', project.id)
            ])

    #########################################

    # category = fields.Selection(
    #     related='project_id.category',
    #     store=False,
    #     readonly=True,
    # )

    def _compute_subtask_count(self):
        for rec in self:
            rec.subtask_count = self.env['project.subtask'].search_count([
                ('project_id', '=', rec.id)
            ])

    def action_view_project_subtasks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subtasks',
            'res_model': 'project.subtask',
            'view_mode': 'kanban,list,form,timeline,activity,pivot',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id
            }
        }

    user_story_count = fields.Integer(
        string="User Stories",
        compute="_compute_story_count"
    )

    def _compute_story_count(self):
        for rec in self:
            rec.user_story_count = self.env['project.user.story'].search_count([
                ('project_id', '=', rec.id)
            ])

    def action_view_project_user_stories(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'User Stories',
            'res_model': 'project.user.story',
            'view_mode': 'kanban,list,form,timeline,activity,pivot',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id
            }
        }

    def _compute_last_update_color(self):
        # Update the mapping to include your 'new' status
        # and any other custom statuses you added
        mapping = {**STATUS_COLOR, 'new': 4}  # 4 is Light Blue, choose 0-11
        for project in self:
            # Safe get to prevent future KeyErrors
            project.last_update_color = mapping.get(project.last_update_status, 0)

    # @api.model
    # def _cron_roll_expected_dates_global(self):
    #
    #     today = fields.Date.today()
    #
    #     models_to_update = [
    #         'project.subtask',
    #         'project.task',
    #         'project.user.story',
    #         'project.epic',
    #         'product.backlog',
    #         'project.project',
    #     ]
    #
    #     for model_name in models_to_update:
    #         model = self.env[model_name]
    #
    #         records = model.search([
    #             ('completed_date', '=', False),
    #             ('planned_end_date', '!=', False),
    #         ])
    #
    #         for rec in records:
    #             if rec.expected_end_date and rec.expected_end_date < today:
    #                 rec.write({
    #                     'expected_end_date': today
    #                 })

    @api.model
    def _cron_roll_expected_dates_global(self):
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)

        models_to_update = [
            'project.subtask',
            'project.task',
            'project.user.story',
            'project.epic',
            'product.backlog',
            'project.project',
        ]

        for model_name in models_to_update:
            model = self.env[model_name].sudo()

            records = model.search([
                ('completed_date', '=', False),
                '|',
                ('planned_end_date', '!=', False),
                ('expected_end_date', '!=', False),
            ])

            for rec in records:
                vals = {}

                if not rec.expected_end_date and rec.planned_end_date:
                    vals['expected_end_date'] = rec.planned_end_date + timedelta(days=1)

                elif rec.expected_end_date and rec.expected_end_date <= today:
                    vals['expected_end_date'] = tomorrow

                if vals:
                    rec.with_context(
                        skip_scheduler_chain=True,
                        skip_deadline_access_check=True,
                        skip_project_readonly_check=True,
                        allow_governance_write=True,
                        from_kanban_drag_auto=True,
                    ).sudo().write(vals)



    def action_open_sla_selector(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': 'sla.monitor.selector',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_project_id': self.id,
            },
        }

    def action_open_sprint(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sprints',
            'res_model': 'project.sprint',

            # ✅ tree → list (VERY IMPORTANT)
            'view_mode': 'kanban,list,form,calendar,pivot,graph',

            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_start_date': self.planned_start_date,
                'default_end_date': self.planned_end_date,
            },
            'target': 'current',
        }

    product_backlog_ids = fields.One2many(
        'product.backlog',
        'project_id',
        string="Product Backlogs"
    )


    project_progress = fields.Float(
        string="Project Progress %",
        compute="_compute_project_progress",
        store=True
    )

    @api.depends(
        'enable_backlog_flow',

        'product_backlog_ids',
        'product_backlog_ids.backlog_progress',
        'product_backlog_ids.epic_ids.epic_progress',

        'user_story_ids',
        'user_story_ids.task_avg_progress',
        'user_story_ids.task_ids.task_progress',
    )
    def _compute_project_progress(self):
        for project in self:

            if project.enable_backlog_flow:
                backlogs = project.product_backlog_ids
                vals = backlogs.mapped('backlog_progress')
            else:
                stories = project.user_story_ids
                vals = stories.mapped('task_avg_progress')

            project.project_progress = sum(vals) / len(vals) if vals else 0.0

    progress_color = fields.Char(
        string="Progress Color",
        compute="_compute_progress_color",
        store=False
    )

    @api.depends("project_progress")
    def _compute_progress_color(self):
        # get first config (assuming single master config)
        config = self.env['progress.config'].search([], limit=1)

        lines = config.line_ids.sorted(key=lambda l: l.min_value) if config else []

        for rec in self:
            color = 'bg-primary'  # fallback

            for line in lines:
                if line.min_value <= rec.project_progress <= line.max_value:
                    color = line.color
                    break

            rec.progress_color = color

###########################################################################

    sla_last_notified_stage = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
        ('red_3', 'Red +3'),
        ('red_6', 'Red +6'),
    ], copy=False)

    sla_last_notified_date = fields.Date(copy=False)

    @api.model
    def _cron_recompute_project_sla(self):
        projects = self.search([
            ('planned_end_date', '!=', False),
            ('is_project_done', '=', False),
        ])
        projects._compute_backlog_sla()

    @api.model
    def _cron_project_sla_email(self):

        domain = [
            ('is_project_done', '=', False),
            ('planned_end_date', '!=', False),
            ('sla_stage', 'in', ['amber', 'red', 'red_3', 'red_6']),
        ]

        batch_size = 200
        offset = 0

        template_map = {
            'amber': 'project_main_mgmt.email_template_project_sla_amber',
            'red': 'project_main_mgmt.email_template_project_sla_red',
            'red_3': 'project_main_mgmt.email_template_project_sla_red_3',
            'red_6': 'project_main_mgmt.email_template_project_sla_red_6',
        }

        # ✅ Dynamic Sender: No more searching for 'Gmail SMTP' or hardcoded strings
        email_from = (
                self.env['ir.config_parameter'].sudo().get_param('mail.default.from')
                or self.env.company.email
        )
        while True:
            projects = self.search(domain, limit=batch_size, offset=offset)
            if not projects:
                break

            offset += batch_size

            for project in projects:
                try:
                    stage = project.sla_stage

                    # prevent duplicate
                    if project.sla_last_notified_stage == stage:
                        continue

                    users = self._get_sla_users(project, stage)

                    partners = users.mapped('partner_id').filtered(
                        lambda p: p.email
                    )

                    if not partners:
                        _logger.warning(f"No recipients for project {project.id}")
                        continue

                    template = self.env.ref(
                        template_map.get(stage),
                        raise_if_not_found=False
                    )

                    if not template:
                        _logger.error(f"Missing template for stage {stage}")
                        continue

                    template.send_mail(
                        project.id,
                        force_send=True,
                        email_values={
                            'email_from': email_from,
                            'recipient_ids': [(6, 0, partners.ids)],
                        }
                    )

                    project.sla_last_notified_stage = stage
                    project.sla_last_notified_date = fields.Date.today()

                except Exception:
                    _logger.exception(f"SLA email failed for project {project.id}")

    def _get_sla_users(self, project, stage):

        if stage == 'amber':
            return project.sla_amber_user_ids

        elif stage == 'red':
            return project.sla_red_user_ids

        elif stage == 'red_3':
            return project.sla_overdue_3_user_ids


        elif stage == 'red_6':
            return project.sla_overdue_6_user_ids

        return self.env['res.users']


    ###############################################

    def _check_project_kanban_drag_access(self):

        for rec in self:
            if rec._is_full_project_manager_access():
                continue

            if not rec._current_user_has_kanban_drag_access():
                raise AccessError(_("You do not have Kanban Drag & Drop access for this project."))

    def _current_user_has_kanban_drag_access(self):
        self.ensure_one()
        # Admin / Program Manager / Project Manager -> always allowed
        if self._is_full_project_manager_access():
            return True
        return self._current_user_has_access_anywhere_in_project([
            'project_main_mgmt.mt_project_kanban_drag_access',
            'project_main_mgmt.mt_project_product_backlog_kanban_drag_access',
            'project_main_mgmt.mt_project_epic_kanban_drag_access',
            'project_main_mgmt.mt_project_user_story_kanban_drag_access',
            'project_main_mgmt.mt_project_task_kanban_drag_access',
            'project_main_mgmt.mt_project_subtask_kanban_drag_access',
        ])

    def _current_user_has_governance_access(self):
        self.ensure_one()
        # Admin / Program Manager / Project Manager -> always allowed
        if self._is_full_project_manager_access():
            return True

        return self._current_user_has_access_anywhere_in_project([
            'project_main_mgmt.mt_project_governance_access',
            'project_main_mgmt.mt_project_product_backlog_governance_access',
            'project_main_mgmt.mt_project_epic_governance_access',
            'project_main_mgmt.mt_project_user_story_governance_access',
            'project_main_mgmt.mt_project_task_governance_access',
            'project_main_mgmt.mt_project_subtask_governance_access',
        ])

    def _check_project_deadline_change_access(self):

        for rec in self:
            # Admin / Program Manager / Project Manager -> full access
            if rec._is_full_project_manager_access():
                continue
            if not rec._current_user_has_deadline_change_access():
                raise AccessError(_("You do not have Changing Deadline access for this project."))

    def _current_user_has_deadline_change_access(self):
        self.ensure_one()
        # Admin / Program Manager / Project Manager -> always allowed
        if self._is_full_project_manager_access():
            return True

        return self._current_user_has_access_anywhere_in_project([
            'project_main_mgmt.mt_project_deadline_change_access',
            'project_main_mgmt.mt_project_product_backlog_deadline_access',
            'project_main_mgmt.mt_project_epic_deadline_access',
            'project_main_mgmt.mt_project_user_story_deadline_access',
            'project_main_mgmt.mt_project_task_deadline_access',
            'project_main_mgmt.mt_project_subtask_deadline_access',
        ])

    def _is_project_user_readonly_mode(self):
        for rec in self:
            if rec._is_full_project_manager_access():
                return False

        # Project users remain readonly
        return self.env.user.has_group('project.group_project_user')

    def _check_project_readonly_access(self, vals):

        if self.env.context.get('skip_project_readonly_check'):
            return

        if not self._is_project_user_readonly_mode():
            return
        # for rec in self:
        #     if rec._is_full_project_manager_access():
        #         return

        allowed_fields = {
            # chatter
            'message_follower_ids',
            'assignee_id',
            'message_partner_ids',
            'message_ids',

            # governance
            'project_approver_ids',
            'approved_by_id',
            'is_project_done',
            'evidence_required',

            # deadline
            'planned_start_date',
            'planned_end_date',
            'expected_end_date',
            'completed_date',

            # kanban
            'stage_id',
            'kanban_state',
            'status',
            'state',
            'sequence',
            'date_last_stage_update',

            # timesheet
            'timesheet_ids',
            'timesheet_line_ids',
            'account_analytic_line_ids',
        }

        technical_ok = {
            'write_date',
            'write_uid',
            '__last_update',
        }

        forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
        if forbidden:
            raise AccessError(_("Project is read-only. You can only use Chatter."))

    # def _check_project_readonly_access(self, vals):
    #     # 1. Check if the mode is actually active
    #     readonly_mode = self._is_project_user_readonly_mode()
    #     _logger.info(">>> DEBUG: Readonly Mode Active: %s", readonly_mode)
    #
    #     if not readonly_mode:
    #         return
    #
    #     allowed_fields = {
    #         'message_follower_ids', 'message_partner_ids', 'message_ids',
    #         'project_approver_ids', 'approved_by_id', 'is_project_done',
    #         'evidence_required', 'planned_start_date', 'planned_end_date',
    #         'expected_end_date', 'completed_date', 'stage_id', 'kanban_state',
    #         'status', 'state', 'sequence', 'date_last_stage_update',
    #         'timesheet_ids', 'timesheet_line_ids', 'account_analytic_line_ids',
    #     }
    #
    #     technical_ok = {'write_date', 'write_uid', '__last_update'}
    #
    #     # 2. Identify the exact field being rejected
    #     incoming_fields = set(vals.keys())
    #     forbidden = (incoming_fields - technical_ok) - allowed_fields
    #
    #     if forbidden:
    #         _logger.error(">>> DEBUG: BLOCKING WRITE. Forbidden fields: %s", forbidden)
    #         _logger.error(">>> DEBUG: Vals received: %s", vals)
    #         raise AccessError(
    #             _("Project is read-only. You can only use Chatter. (Blocked fields: %s)" % list(forbidden)))

    def check_access_rule(self, operation):
        if operation in ('write', 'unlink'):
            for rec in self:
                # Admin / Program Manager / Project Manager -> full access
                if rec._is_full_project_manager_access():
                    continue
                if (
                        operation == 'write'
                        and self.env.context.get('from_project_approval')
                        and rec._is_current_user_project_approver()
                ):
                    continue

                # Optional kanban special access for write
                if operation == 'write' and rec._current_user_has_kanban_drag_access():
                    continue

                break
            else:
                return

        return super().check_access_rule(operation)

    program_manager_id = fields.Many2one(
        'res.users',
        string='Program Manager',
        index=True
    )

    @api.constrains('user_id', 'program_manager_id')
    def _check_manager_difference(self):
        for rec in self:
            if rec.user_id and rec.program_manager_id and rec.user_id == rec.program_manager_id:
                raise ValidationError("Project Manager and Program Manager cannot be the same.")

    def _is_full_project_manager_access(self):
        self.ensure_one()

        # Real admin
        if self.env.user.has_group('base.group_system'):
            return True

        # Assigned Program Manager
        if self.program_manager_id and self.program_manager_id.id == self.env.user.id:
            return True

        # Assigned Project Manager
        if self.user_id and self.user_id.id == self.env.user.id:
            return True

        return False

    def _current_user_has_access_anywhere_in_project(self, subtype_xmlids):
        self.ensure_one()

        # Admin / Program Manager / Project Manager -> always allowed
        if self._is_full_project_manager_access():
            return True

        partner = self.env.user.partner_id
        if not partner:
            return False

        subtype_ids = []
        for xmlid in subtype_xmlids:
            subtype = self.env.ref(xmlid, raise_if_not_found=False)
            if subtype:
                subtype_ids.append(subtype.id)

        if not subtype_ids:
            return False

        backlog_ids = self.env['product.backlog'].search([
            ('project_id', '=', self.id)
        ]).ids or [0]

        epic_ids = self.env['project.epic'].search([
            ('project_id', '=', self.id)
        ]).ids or [0]

        story_ids = self.env['project.user.story'].search([
            ('project_id', '=', self.id)
        ]).ids or [0]

        task_ids = self.env['project.task'].search([
            ('project_id', '=', self.id)
        ]).ids or [0]

        subtask_ids = self.env['project.subtask'].search([
            ('project_id', '=', self.id)
        ]).ids or [0]

        follower = self.env['mail.followers'].search([
            ('partner_id', '=', partner.id),
            ('subtype_ids', 'in', subtype_ids),
            '|', '|', '|', '|', '|',
            '&', ('res_model', '=', 'project.project'), ('res_id', '=', self.id),
            '&', ('res_model', '=', 'product.backlog'), ('res_id', 'in', backlog_ids),
            '&', ('res_model', '=', 'project.epic'), ('res_id', 'in', epic_ids),
            '&', ('res_model', '=', 'project.user.story'), ('res_id', 'in', story_ids),
            '&', ('res_model', '=', 'project.task'), ('res_id', 'in', task_ids),
            '&', ('res_model', '=', 'project.subtask'), ('res_id', 'in', subtask_ids),
        ], limit=1)

        return bool(follower)


    def _is_current_user_project_approver(self):
       self.ensure_one()
       return self.env.user in self.project_approver_ids

    # timesheet_access_user_ids = fields.Many2many(
    #     'res.users',
    #     string="Timesheet / Timer Access Users"
    # )
    timesheet_access_user_ids = fields.Many2many(
        'res.users',
        'project_project_timesheet_access_rel',  # DIFFERENT relation table
        'project_id',
        'user_id',
        string="Timesheet / Timer Access Users"
    )

    def _current_user_has_timesheet_access(self):
        self.ensure_one()
        print("TIMESHEET ACCESS CHECK USER:", self.env.user.name)
        print("IS ADMIN:", self.env.user.has_group('base.group_system'))
        print("IS PROJECT USER:", self.env.user.has_group('project.group_project_user'))
        print("IS TIMESHEET USER:", self.env.user.has_group('hr_timesheet.group_hr_timesheet_user'))
        print("IS FULL PM ACCESS:", self._is_full_project_manager_access())

        # Admin
        if self.env.user.has_group('base.group_system'):
            return True

        # Program Manager / Project Manager full access
        if self._is_full_project_manager_access():
            return True

        # Normal project user must have Timesheet group
        if self.env.user.has_group('project.group_project_user') and self.env.user.has_group(
                'hr_timesheet.group_hr_timesheet_user'):
            return True

        return False



    @api.depends(
        'message_partner_ids',
        'product_backlog_ids.message_partner_ids',
        'epic_ids.message_partner_ids',
        'user_story_ids.message_partner_ids',
        'task_ids.message_partner_ids',
        'task_ids.user_ids',
        'subtask_ids.message_partner_ids',
        'subtask_ids.assignee_id',
        'program_manager_id',
        'user_id',
    )
    def _compute_access_user_ids(self):
        for rec in self:
            users = self.env['res.users']

            # Managers
            if rec.program_manager_id:
                users |= rec.program_manager_id
            if rec.user_id:
                users |= rec.user_id

            # Followers on project
            users |= rec.message_partner_ids.mapped('user_ids')

            # Followers anywhere under project
            users |= rec.product_backlog_ids.mapped('message_partner_ids.user_ids')
            users |= rec.epic_ids.mapped('message_partner_ids.user_ids')
            users |= rec.user_story_ids.mapped('message_partner_ids.user_ids')
            users |= rec.task_ids.mapped('message_partner_ids.user_ids')
            users |= rec.subtask_ids.mapped('message_partner_ids.user_ids')

            # Assignees
            users |= rec.task_ids.mapped('user_ids')
            users |= rec.subtask_ids.mapped('assignee_id')

            rec.access_user_ids = [(6, 0, users.ids)]

    @api.depends(
        'task_ids.allow_timesheet_user_ids',
        'task_ids.subtask_ids.allow_timesheet_user_ids'
    )
    def _compute_timesheet_users(self):
        for project in self:
            users = project.task_ids.mapped('allow_timesheet_user_ids')
            users |= project.task_ids.mapped('subtask_ids.allow_timesheet_user_ids')
            project.timesheet_user_ids = users

class SlaMonitorSelector(models.TransientModel):
    _name = 'sla.monitor.selector'
    _description = 'SLA Monitoring Selector'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True
    )
    enable_backlog_flow = fields.Boolean(
        related='project_id.enable_backlog_flow',
        readonly=True
    )

    sla_level = fields.Selection(
        [
            ('project', 'Project'),
            ('backlog', 'Product Backlog'),
            ('epic', 'Epic'),
            ('story', 'User Story'),
            ('task', 'Task'),
            ('subtask', 'Subtask'),
        ],
        string='SLA Level',
        default='project',
        required=True
    )

    # ADD this dummy field to handle the "OFF" state UI
    sla_level_restricted = fields.Selection([
        ('project', 'Project'),
        ('story', 'User Story'),
        ('task', 'Task'),
        ('subtask', 'Subtask'),
    ], string='SLA Level')

    # Sync them together so 'sla_level' always has the value
    @api.onchange('sla_level_restricted')
    def _sync_to_main_field(self):
        if not self.enable_backlog_flow:
            self.sla_level = self.sla_level_restricted

    @api.onchange('sla_level')
    def _sync_to_dummy_field(self):
        if not self.enable_backlog_flow:
            self.sla_level_restricted = self.sla_level



    project_ids = fields.Many2many('project.project' )
    backlog_ids = fields.Many2many('product.backlog')
    epic_ids = fields.Many2many('project.epic')
    story_ids = fields.Many2many('project.user.story')
    task_ids = fields.Many2many('project.task')
    subtask_ids = fields.Many2many('project.subtask')

    @api.onchange('project_id', 'sla_level')
    def _onchange_load_sla_records(self):
        self.update({
            'project_ids': [Command.clear()],
            'backlog_ids': [Command.clear()],
            'epic_ids': [Command.clear()],
            'story_ids': [Command.clear()],
            'task_ids': [Command.clear()],
            'subtask_ids': [Command.clear()],

        })

        if not self.project_id:
            return


        if self.sla_level == 'project':
            self.project_ids = [Command.set(self.project_id.ids)]

        elif self.sla_level == 'backlog':
            recs = self.env['product.backlog'].search([
                ('project_id', '=', self.project_id.id),
                ('is_done', 'in', [True, False]),
                # ('is_done', '=', False),
            ])
            self.backlog_ids = [Command.set(recs.ids)]

        elif self.sla_level == 'epic':
            recs = self.env['project.epic'].search([
                ('project_id', '=', self.project_id.id),
                # ('is_done', '=', False),
            ])
            self.epic_ids = [Command.set(recs.ids)]

        elif self.sla_level == 'story':

            recs = self.env['project.user.story'].search([
                # ('is_done', '=', False),
                '|',
                ('epic_id.project_id', '=', self.project_id.id),
                ('project_id', '=', self.project_id.id),
            ])

            self.story_ids = [Command.set(recs.ids)]


        elif self.sla_level == 'task':

            recs = self.env['project.task'].search([
                ('project_id', '=', self.project_id.id),
                # ('status', '!=', 'done'),
            ])

            self.task_ids = [Command.set(recs.ids)]

        elif self.sla_level == 'subtask':  # ✅ ADD THIS BLOCK
            recs = self.env['project.subtask'].search([
                ('project_id', '=', self.project_id.id),
            ])
            self.subtask_ids = [Command.set(recs.ids)]

class ProjectTaskTypeMaster(models.Model):
    _name = 'project.task.type.master'
    _description = 'Task Type Configuration'

    name = fields.Char(required=True)

    applies_to = fields.Selection([
        ('task', 'Task'),
        ('subtask', 'Subtask')
    ], required=True, default='task')


class ProjectTaskLabelMaster(models.Model):
    _name = 'project.task.label.master'
    _description = 'Task label Configuration'

    name = fields.Char(required=True)

    applies_to = fields.Selection([
    ('task', 'Task'),
    ('subtask', 'Subtask')
    ], required=True, default='task')

