from odoo import models, fields

class EstateFarmSales(models.Model):
    _name = 'estate.farm.sales'
    _inherit = ['mail.thread','mail.activity.mixin',  'estate.security.mixin']  # <-- Enable followers & chatter
    _description = 'Post-Harvest & Sales'
    _order = "id desc"

    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    crop_id = fields.Many2one('estate.crop.name', string="Crop / Batch ID", tracking=True)
    harvest_date = fields.Date(tracking=True)
    processing_details = fields.Text(tracking=True)
    storage_location_id = fields.Many2one('estate.room', string="Storage Location", tracking=True)
    buyer_info = fields.Char(tracking=True)
    contract_invoice = fields.Char(tracking=True)
    logistics_notes = fields.Text(tracking=True)
