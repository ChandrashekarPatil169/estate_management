from odoo import models, fields

class CustomLocationInherit(models.Model):
    _inherit = 'custom.location'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    property_id = fields.Many2one(
        'estate.property',
        string="Property",tracking=True
    )

    building_id = fields.Many2one(
        'estate.building',
        string="Building",tracking=True
    )

