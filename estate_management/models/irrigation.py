from odoo import models, fields

class EstateIrrigation(models.Model):
    _name = 'estate.irrigation'
    _description = 'Irrigation Log'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']  # <-- enables followers & chatter
    _order = "id desc"
    # _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    plot_id = fields.Many2one('estate.farm.plot', string="Plot", tracking=True)
    date_time = fields.Datetime(string="Date / Time", tracking=True)
    water_source = fields.Char(tracking=True)
    irrigation_type = fields.Selection([('drip','Drip'),('sprinkler','Sprinkler'),('flood','Flood')], tracking=True)
    volume_used = fields.Float(string="Volume of Water Used (Liters)", tracking=True)
    operator_id = fields.Many2one('hr.employee', string="Operator",tracking=True)
