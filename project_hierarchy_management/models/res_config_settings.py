from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    project_creator_user_ids = fields.Many2many(
        'res.users',
        string="Allowed Project Creators",
        help="Only selected users can create projects"
    )

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'project.allowed_creator_user_ids',
            ','.join(map(str, self.project_creator_user_ids.ids))
        )

    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo().get_param(
            'project.allowed_creator_user_ids', ''
        )
        res['project_creator_user_ids'] = [
            (6, 0, list(map(int, param.split(','))) if param else [])
        ]
        return res
