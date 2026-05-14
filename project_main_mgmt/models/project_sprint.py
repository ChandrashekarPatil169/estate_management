from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class ProjectSprint(models.Model):
    _name = 'project.sprint'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Project Sprint'
    _order = 'start_date desc'

    name = fields.Char(required=True)

    # project_id = fields.Many2one(
    #     'project.project',
    #     required=True,
    #     ondelete='cascade',
    #     index=True
    # )
    scope_line_ids = fields.One2many(
        'project.sprint.line',
        'sprint_id',
        string='Sprint Scope'
    )

    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    project_id = fields.Many2one('project.project', required=True)
    description = fields.Html(string="Notes")


    user_story_ids = fields.Many2many(
        'project.user.story',
        'project_sprint_story_rel',
        'sprint_id',
        'story_id',
        string='User Stories'
    )

    task_ids = fields.Many2many(
        'project.task',
        'project_sprint_task_rel',
        'sprint_id',
        'task_id',
        string='Tasks'
    )

    subtask_ids = fields.Many2many(
        'project.subtask',
        'project_sprint_subtask_rel',
        'sprint_id',
        'subtask_id',
        string='Sub Tasks'
    )

    stage_id = fields.Many2one(
        'project.sprint.stage',
        string='Stage',
        group_expand='_read_group_stage_ids',
        ondelete='restrict',
        index=True,
        tracking=True,
        default=lambda self: self._default_stage_id()
    )


    #######################for cron job########################
    # Tracking flags
    start_mail_sent = fields.Boolean(default=False, copy=False)
    mid_mail_sent = fields.Boolean(default=False, copy=False)
    done_mail_sent = fields.Boolean(default=False, copy=False)

    @api.model
    def create(self, vals):
        """ Auto-subscribe project followers on creation """
        record = super().create(vals)
        if record.project_id:
            record.message_subscribe(partner_ids=record.project_id.message_partner_ids.ids)
        return record

    def write(self, vals):
        # 1. Update the record first
        res = super(ProjectSprint, self).write(vals)

        # 2. Check if stage_id was changed
        if 'stage_id' in vals:
            for rec in self:
                # If the new stage is 'Folded' (Done) and mail wasn't sent
                if rec.stage_id.fold and not rec.done_mail_sent:
                    _logger.info("Sprinting Done: Sending mail for %s", rec.name)

                    # Send the mail using your template
                    rec._send_sprint_email('project_main_mgmt.mail_template_sprint_done')

                    # Mark as sent so it doesn't trigger again
                    rec.done_mail_sent = True
        return res

    @api.model
    def _cron_sprint_notifications(self):
        """ Daily check for Start and Mid-point """
        today = fields.Date.today()
        sprints = self.search([
            ('start_date', '!=', False),
            ('end_date', '!=', False),
            '|', ('start_mail_sent', '=', False), ('mid_mail_sent', '=', False)
        ])

        for sprint in sprints:
            # --- START MAIL ---
            if sprint.start_date <= today and not sprint.start_mail_sent:
                sprint._send_sprint_email('project_main_mgmt.mail_template_sprint_start')
                sprint.write({'start_mail_sent': True})

            # --- MIDPOINT MAIL ---
            total_days = (sprint.end_date - sprint.start_date).days
            if total_days > 0 and not sprint.mid_mail_sent:
                mid_date = sprint.start_date + timedelta(days=total_days // 2)
                if today >= mid_date:
                    sprint._send_sprint_email('your_module.mail_template_sprint_mid')
                    sprint.write({'mid_mail_sent': True})

    def _send_sprint_email(self, template_xmlid):
        """ Sends the email to followers using Odoo 19 logic """
        template = self.env.ref(template_xmlid, raise_if_not_found=False)
        if template:
            for record in self:
                # Fallback logic for Author: Project Manager -> Creator -> Current User
                author = record.project_id.user_id.partner_id or record.create_uid.partner_id or self.env.user.partner_id

                # Render the body and subject
                body = template._render_field('body_html', record.ids)[record.id]
                subject = template._render_field('subject', record.ids)[record.id]

                record.message_post(
                    body=body,
                    subject=subject,
                    author_id=author.id,  # This tells the mail server WHO is sending it
                    email_from=author.email_formatted,  # This ensures the 'From' header is valid
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment',
                )

    ###########################################################

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None, **kwargs):
        return self.env['project.sprint.stage'].search([])

    def _default_stage_id(self):
        # Prevent crash if the table hasn't been created yet during module install
        if not self.env.registry.ready:
            return False
        try:
            return self.env['project.sprint.stage'].search([], limit=1).id
        except:
            return False

    # ---------------- ONCHANGE LOGIC ----------------
    @api.onchange('project_id')
    def _onchange_project(self):
        if not self.project_id:
            return

        if not self.start_date:
            self.start_date = self.project_id.planned_start_date

        if not self.end_date:
            self.end_date = self.project_id.planned_end_date

    @api.onchange('user_story_ids')
    def _onchange_user_story_ids(self):
        # Clear dependent fields
        self.task_ids = False
        self.subtask_ids = False

        return {
            'domain': {
                'task_ids': [
                    ('story_id', 'in', self.user_story_ids.ids)
                ]
            }
        }

    @api.onchange('task_ids')
    def _onchange_task_ids(self):
        self.subtask_ids = False

        return {
            'domain': {
                'subtask_ids': [
                    ('task_id', 'in', self.task_ids.ids)
                ]
            }
        }

class ProjectSprintLine(models.Model):
    _name = 'project.sprint.line'
    _description = 'Sprint Scope Line'


    sprint_id = fields.Many2one(
        'project.sprint',
        required=True,
        ondelete='cascade'
    )

    project_id = fields.Many2one(
        related='sprint_id.project_id',
        store=True,
        readonly=True
    )

    user_story_id = fields.Many2one(
        'project.user.story',
        required=True,
        domain="[('project_id', '=', project_id)]"
    )

    task_id = fields.Many2one(
        'project.task',
        domain="[('story_id', '=', user_story_id)]"
    )

    subtask_id = fields.Many2one(
        'project.subtask',
        domain="[('task_id', '=', task_id)]"
    )

    @api.onchange('user_story_id')
    def _onchange_user_story_id(self):
        self.task_id = False
        self.subtask_id = False
        return {
            'domain': {
                'user_story_id': [('project_id', '=', self.project_id.id)],
                'task_id': [('story_id', '=', self.user_story_id.id)],
            }
        }

    @api.onchange('task_id')
    def _onchange_task_id(self):
        self.subtask_id = False
        return {
            'domain': {
                'subtask_id': [('task_id', '=', self.task_id.id)],
            }
        }

class ProjectSprintStage(models.Model):
    _name = 'project.sprint.stage'
    _description = 'Sprint Stage'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=1)
    fold = fields.Boolean(string='Folded in Kanban')
