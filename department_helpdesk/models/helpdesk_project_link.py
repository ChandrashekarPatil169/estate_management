from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    project_id = fields.Many2one('project.project', string="Project")

    task_count = fields.Integer(compute="_compute_task_count")

    user_story_ids = fields.One2many(
        'project.user.story',
        compute="_compute_user_story_ids",
        string="User Stories"
    )
    user_story_id = fields.Many2one(
        'project.user.story',
        string="User Story"
    )

    @api.onchange('project_id')
    def _onchange_project(self):
        self.user_story_id = False

    def _compute_user_story_ids(self):
        for rec in self:
            if rec.project_id:
                rec.user_story_ids = self.env['project.user.story'].search([
                    ('project_id', '=', rec.project_id.id)
                ])
            else:
                rec.user_story_ids = False

    def _compute_task_count(self):
        for rec in self:
            rec.task_count = self.env['project.task'].search_count([
                ('helpdesk_ticket_id', '=', rec.id)
            ])

    def action_view_tasks(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Tasks',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [('helpdesk_ticket_id', '=', self.id)],
            'context': {
                'default_helpdesk_ticket_id': self.id,
                'default_project_id': self.project_id.id,
                'default_story_id': self.user_story_id.id,
            }
        }

class ProjectTask(models.Model):
    _inherit = 'project.task'

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket')

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            # ✅ SAFE injection (non-breaking)
            if vals.get('helpdesk_ticket_id') and not vals.get('project_id'):

                ticket = self.env['helpdesk.ticket'].browse(vals['helpdesk_ticket_id'])

                if ticket.project_id:
                    vals['project_id'] = ticket.project_id.id

        # ✅ THIS CALLS YOUR ORIGINAL LOGIC (VERY IMPORTANT)
        return super().create(vals_list)