from odoo import models, fields

class EstateFarmCompliance(models.Model):
    _name = 'estate.farm.compliance'
    _description = 'Farm Compliance & Sustainability'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']  # <-- enable chatter & followers
    _order = "id desc"

    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    organic_certification = fields.Boolean(tracking=True)
    fairtrade_certification = fields.Boolean(tracking=True)
    rainforest_certification = fields.Boolean(tracking=True)
    environmental_metrics = fields.Text(tracking=True)
    pesticide_compliance = fields.Text(tracking=True)
    government_permits = fields.Text(tracking=True)
