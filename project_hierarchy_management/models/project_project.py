from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError

class ProjectProject(models.Model):
    _inherit = 'project.project'

    # UI helper
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
    # sub_project_count = fields.Integer(string="Temporary Helper", default=0)

    # ------------------------------------------------
    # Reject button → open wizard
    # ------------------------------------------------
    def action_open_reject_wizard(self):
        self.ensure_one()

        if self.state != 'draft':
            raise ValidationError(_("Only Draft projects can be rejected."))

        if not self.is_current_user_approver:
            raise AccessError(_("You are not allowed to reject projects."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Project'),
            'res_model': 'project.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
            }
        }

    # ------------------------------------------------
    # Helpers
    # ------------------------------------------------
    def _get_approver_user_ids(self):
        return set(
            self.env['project.approval.matrix'].sudo().search([
                ('active', '=', True)
            ]).mapped('user_id.id')
        )

    # def _compute_is_current_user_approver(self):
    #     approvers = self._get_approver_user_ids()
    #     uid = self.env.user.id
    #     is_admin = self.env.user.has_group('base.group_system')
    #
    #     for rec in self:
    #         rec.is_current_user_approver = is_admin or uid in approvers
    def _compute_is_current_user_approver(self):
        approvers = self._get_approver_user_ids()
        uid = self.env.user.id
        is_admin = self.env.user.has_group('base.group_system')

        for rec in self:
            rec.is_current_user_approver = (
                    is_admin
                    or uid in approvers
                    or (rec.user_id and rec.user_id.id == uid)
                    or (hasattr(rec,
                                'program_manager_id') and rec.program_manager_id and rec.program_manager_id.id == uid)
            )
    # ------------------------------------------------
    # Actions
    # ------------------------------------------------
    # def _is_user_allowed_to_approve(self):
    #     self.ensure_one()
    #
    #     approver_ids = set(
    #         self.env['project.approval.matrix']
    #         .sudo()
    #         .search([('active', '=', True)])
    #         .mapped('user_id.id')
    #     )
    #
    #     return (
    #             self.env.user.has_group('base.group_system')
    #             or self.env.user.id in approver_ids
    #     )
    def _is_user_allowed_to_approve(self):
        self.ensure_one()

        approver_ids = set(
            self.env['project.approval.matrix']
            .sudo()
            .search([('active', '=', True)])
            .mapped('user_id.id')
        )

        uid = self.env.user.id

        return (
                self.env.user.has_group('base.group_system')
                or uid in approver_ids
                or (self.user_id and self.user_id.id == uid)
                or (hasattr(self,
                            'program_manager_id') and self.program_manager_id and self.program_manager_id.id == uid)
        )

    # def _get_next_stage(self):
    #     self.ensure_one()
    #
    #     Stage = self.env['project.project.stage']
    #
    #     current_stage = self.stage_id
    #     if not current_stage:
    #         raise ValidationError(_("Project has no current stage."))
    #
    #     next_stage = Stage.search([
    #         ('sequence', '>', current_stage.sequence),
    #         ('company_id', 'in', [self.company_id.id, False]),
    #     ], order='sequence asc', limit=1)
    #
    #     if not next_stage:
    #         raise ValidationError(_("No next stage configured after approval."))
    #
    #     return next_stage
    def _get_next_stage(self):
        self.ensure_one()

        project_sudo = self.sudo()
        Stage = self.env['project.project.stage'].sudo()

        current_stage = project_sudo.stage_id
        if not current_stage:
            raise ValidationError(_("Project has no current stage."))

        next_stage = Stage.search([
            ('sequence', '>', current_stage.sequence),
            ('company_id', 'in', [project_sudo.company_id.id, False]),
        ], order='sequence asc', limit=1)

        if not next_stage:
            raise ValidationError(_("No next stage configured after approval."))

        return next_stage

    def action_approve(self):
        for project in self:
            if project.state != 'draft':
                raise ValidationError(_("Only Draft projects can be approved."))

            if not project._is_user_allowed_to_approve():
                raise AccessError(_("You are not allowed to approve projects."))

            next_stage = project._get_next_stage()

            # business transition
            project.write({'state': 'approved'})

            # workflow transition
            project.sudo().write({'stage_id': next_stage.id})

    # def action_reject(self):
    #     for project in self:
    #         if project.state != 'draft':
    #             raise ValidationError(_("Only Draft projects can be rejected."))
    #
    #         if not project.is_current_user_approver:
    #             raise AccessError(_("You are not allowed to reject projects."))
    #
    #         project.write({'state': 'canceled'})
    def action_reject(self):
        for project in self:
            if project.state != 'draft':
                raise ValidationError(_("Only Draft projects can be rejected."))

            if not project.is_current_user_approver:
                raise AccessError(_("You are not allowed to reject projects."))

            project.write({'state': 'rejected'})

    # ------------------------------------------------
    # Hard backend enforcement
    # ------------------------------------------------
    # def write(self, vals):
    #     if 'state' in vals:
    #         for project in self:
    #             if project.state == 'draft' and vals['state'] in ('todo', 'canceled'):
    #                 if not project.is_current_user_approver:
    #                     raise AccessError(
    #                         _("Only approvers can approve or reject Draft projects.")
    #                     )
    #     return super().write(vals)
    def write(self, vals):
        if 'state' in vals:
            for project in self:
                if project.state == 'draft' and vals['state'] in ('approved', 'rejected'):
                    if not project.is_current_user_approver:
                        raise AccessError(
                            _("Only approvers, assigned Project Manager, or assigned Program Manager can approve or reject Draft projects.")
                        )
        return super().write(vals)

    can_share_project = fields.Boolean(
        string="Can Share Project",
        compute="_compute_can_share_project"
    )

    def _compute_can_share_project(self):
        uid = self.env.user.id
        is_admin = self.env.user.has_group('base.group_system')

        for rec in self:
            rec.can_share_project = (
                    is_admin
                    or (rec.user_id and rec.user_id.id == uid)
                    or (rec.program_manager_id and rec.program_manager_id.id == uid)
            )
