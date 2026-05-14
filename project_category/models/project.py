from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    category = fields.Selection([
        ('software', 'Software'),
        ('hardware', 'Hardware')
    ], string="Category", required=True, default='software', index=True)

    is_software_project = fields.Boolean(
        compute='_compute_is_software',
        store=False
    )

    @api.depends('category')
    def _compute_is_software(self):
        for rec in self:
            rec.is_software_project = rec.category == 'software'
