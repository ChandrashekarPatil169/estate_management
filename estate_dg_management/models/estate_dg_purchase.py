from odoo import models, fields, api
from odoo.exceptions import UserError


class EstateMainStock(models.Model):
    _name = 'estate.stock.main'
    _description = 'Main Fuel Stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    fuel_type_id = fields.Many2one(
        'estate.fuel.type',
        string="Fuel Type",
        required=True
    )

    quantity_available = fields.Float(string="Available Quantity")

    purchase_id = fields.Many2one('estate.dg.purchase')
    refill_id = fields.Many2one('estate.dg.refill')

    source = fields.Selection([
        ('purchase', 'Purchase'),
        ('refill', 'Refill'),
    ])

    date = fields.Date()
    ref = fields.Char()


class EstateDGPurchase(models.Model):
    _name = 'estate.dg.purchase'
    _description = 'DG Fuel Purchase (Main Stock)'
    _rec_name = "fuel_type_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string='Reference')
    date = fields.Date(string='Date', default=fields.Date.context_today, required=True)
    invoice_no = fields.Char(string='Invoice No.')
    supplier = fields.Char(string='Supplier')
    liters = fields.Float(string='Liters')
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount',store=True )
    unit_cost = fields.Float(string='Unit Cost', store=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    fuel_type_id = fields.Many2one(
        'estate.fuel.type',
        string='Fuel Type',
        required=True
    )
    State = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm')],
        default='draft'
    )
    confirm_datetime = fields.Datetime(string="Confirmed On", readonly=True)

    def action_confirm(self):
        for rec in self:
            if rec.State == 'confirm':
                continue
            confirm_time = fields.Datetime.now()

            stock = self.env['estate.stock.main'].search([
                ('fuel_type_id', '=', rec.fuel_type_id.id)
            ], limit=1)

            if stock:
                stock.quantity_available += rec.liters
            else:
                self.env['estate.stock.main'].create({
                    'fuel_type_id': rec.fuel_type_id.id,
                    'quantity_available': rec.liters,
                    'date': confirm_time.date(),
                })
            rec.confirm_datetime = confirm_time
            rec.State = 'confirm'

    @api.depends('liters', 'total_amount')
    def _compute_unit_cost(self):
        for rec in self:
            rec.unit_cost = (rec.total_amount / rec.liters) if rec.liters else 0.0

    @api.depends('unit_cost', 'liters')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = (rec.unit_cost or 0.0) * (rec.liters or 0.0)
