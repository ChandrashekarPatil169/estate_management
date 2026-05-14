from odoo import models, fields, api

class CharterApprovalMatrix(models.Model):
    _name = 'charter.approval.matrix'
    _description = 'Master Charter Approval Matrix'
    _order = 'sequence'

    name = fields.Char(string="Charter Appovers", required=True, default="Standard Charter Process")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    line_ids = fields.One2many('charter.approval.matrix.line', 'matrix_id', string="Approver Steps")

class CharterApprovalMatrixLine(models.Model):
    _name = 'charter.approval.matrix.line'
    _description = 'Master Charter Approval Line'
    _order = 'sequence'

    sequence = fields.Integer(string="Step", default=10)
    matrix_id = fields.Many2one('charter.approval.matrix', ondelete='cascade')
    user_id = fields.Many2one('res.users', string="Approver", required=True)
    # This must be here for the One2many to work
    project_id = fields.Many2one('project.project', ondelete='cascade')