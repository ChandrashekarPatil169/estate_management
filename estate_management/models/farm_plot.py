from odoo import models, fields

class EstateFarmPlot(models.Model):
    _name = 'estate.farm.plot'
    _description = 'Farm Plot'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    code = fields.Char(string="Plot Code / ID", tracking=True)
    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    area = fields.Float(string="Area (acres/hectares)",tracking=True)
    soil_type = fields.Char(tracking=True)
    ph = fields.Float(string="pH",tracking=True)
    drainage_type = fields.Selection([('good','Good'),('poor','Poor'),('average','Average')],tracking=True)
    topography = fields.Char(tracking=True)
    crop_rotation_plan = fields.Text(tracking=True)
