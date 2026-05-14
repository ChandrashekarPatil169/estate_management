from odoo import models, fields


class ProjectApprovalMatrix(models.Model):
    _name = 'project.approval.matrix'
    _description = 'Project Approval Matrix'

    user_id = fields.Many2one(
        'res.users',
        string='Approver',
        required=True,
        ondelete='cascade'
    )
    active = fields.Boolean(default=True)


    _sql_constraints = [
        ('unique_user', 'unique(user_id)', 'This user is already an approver.')
    ]
