from odoo import models, fields,api
from odoo.exceptions import UserError



class MaterialQualityConfig(models.Model):
    _name = 'material.quality.config'
    _description = 'Quality Checker Configuration'

    name = fields.Char(default="QC Settings",tracking=True)
    admin_checker_1 = fields.Many2one('res.users', string="Inventory Department", required=True,tracking=True)
    admin_checker_2 = fields.Many2one('res.users', string="Accounts Department", required=True,tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        # Prevent creating more than one config record
        if self.search_count([]) > 0:
            raise UserError("You can only have one configuration record.")
        return super().create(vals_list)

    def unlink(self):
        # Prevent deletion
        raise UserError("You cannot delete the configuration record.")