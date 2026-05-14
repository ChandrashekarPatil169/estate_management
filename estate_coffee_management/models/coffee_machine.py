from odoo import models, fields

class CoffeeMachine(models.Model):
    _name = 'coffee.machine'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Coffee Machine'
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(string="Machine Name", required=True)
    building_id = fields.Many2one('estate.building', string="Building", required=True)
    machine_stock_ids = fields.One2many('machine.stock', 'machine_id', string="Machine Stock")
