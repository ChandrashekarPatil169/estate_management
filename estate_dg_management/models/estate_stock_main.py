from odoo import models, fields, api

class EstateStockMain(models.Model):
    _name = 'estate.stock.main'
    _description = 'Main Fuel Stock Ledger'
    _order = 'date desc'
    _rec_name ='fuel_type_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date = fields.Date(string='Date',)
    source = fields.Selection([('purchase','Purchase'), ('issue','Issue')], default='purchase')
    ref = fields.Char(string='Reference')
    liters_in = fields.Float(string='Liters In', default=0.0)
    liters_out = fields.Float(string='Liters Out', default=0.0)
    balance = fields.Float(string='Running Balance', compute='_compute_balance', store=True)
    amount = fields.Float(string='Amount')
    purchase_id = fields.Many2one('estate.dg.purchase', string='Purchase')
    refill_id = fields.Many2one('estate.dg.refill', string='Refill')
    fuel_type_id = fields.Many2one(
        'estate.fuel.type',
        string="Fuel Type",
    )
    quantity_available = fields.Float(string="Available Liters", default=0.0)
    purchase_ids = fields.One2many(
        'estate.dg.purchase',
        'fuel_type_id',
        string="Purchases"
    )

    refill_ids = fields.One2many(
        'estate.dg.refill',
        'fuel_type_id',
        string="DG Refills"
    )

    purchase_count = fields.Integer(
        compute="_compute_counts",
        string="Purchase Count"
    )

    refill_count = fields.Integer(
        compute="_compute_counts",
        string="Refill Count"
    )

    def _compute_counts(self):
        for rec in self:
            rec.purchase_count = self.env['estate.dg.purchase'].search_count([
                ('fuel_type_id', '=', rec.fuel_type_id.id),
                ('State', '=', 'confirm')
            ])

            rec.refill_count = self.env['estate.dg.refill'].search_count([
                ('fuel_type_id', '=', rec.fuel_type_id.id),
                ('state', '=', 'confirm')
            ])

    def action_view_purchases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fuel Purchases',
            'res_model': 'estate.dg.purchase',
            'view_mode': 'list,form',
            'domain': [
                ('fuel_type_id', '=', self.fuel_type_id.id),
                ('State', '=', 'confirm')
            ],
            'context': {
                'default_fuel_type_id': self.fuel_type_id.id
            }
        }

    def action_view_refills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'DG Refills',
            'res_model': 'estate.dg.refill',
            'view_mode': 'list,form',
            'domain': [
                ('fuel_type_id', '=', self.fuel_type_id.id),
                ('state', '=', 'confirm')
            ],'context': {
            'default_fuel_type_id': self.fuel_type_id.id
        }

        }

    @api.depends('liters_in', 'liters_out')
    def _compute_balance(self):
        # naive running balance — compute per record based on ordering
        # For simplicity compute per record over all records (not optimized)
        for rec in self:
            all_recs = self.search([('id', '<=', rec.id)], order='id')
            bal = 0.0
            for r in all_recs:
                bal += (r.liters_in or 0.0) - (r.liters_out or 0.0)
            rec.balance = bal
