from odoo import models, fields, api
from odoo.exceptions import UserError


class EstateTankCapacityMaster(models.Model):
    _name = 'estate.tank.capacity.master'
    _description = 'Tank Capacity Master'
    _rec_name = 'capacity_l'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Capacity Name", required=True)
    capacity_l = fields.Float(string="Capacity", required=True)

class EstateFuelType(models.Model):
    _name = 'estate.fuel.type'
    _description = 'Fuel Type Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(required=True)
    code = fields.Char()




class EstateGeneratorMaster(models.Model):
    _name = 'estate.generator.master'
    _description = 'Generator Master'
    _rec_name = 'name'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Generator Name", required=True)
    generator_code = fields.Char(string="Generator Code", required=True)

    building_id = fields.Many2one('estate.building', string="Building", required=True)
    unit_id = fields.Many2one('estate.unit', string="Unit", required=True)
    floor_id = fields.Many2one('estate.floor', string="Floor", required=True)

    _sql_constraints = [
        ('generator_code_unique', 'unique(generator_code)', 'Generator Code must be unique!')
    ]

class EstateDG(models.Model):
    _name = 'estate.dg'
    _description = 'Diesel Generator'
    _rec_name = 'generator_master_id'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    generator_master_id = fields.Many2one(
        'estate.generator.master',
        string="Generator Name",
        required=True
    )
    name = fields.Char(string='Generator Name')
    code = fields.Char(string='Code')
    building_id = fields.Many2one('estate.building', string='Building')
    unit_id = fields.Many2one('estate.unit', string='Unit')
    floor_id = fields.Many2one('estate.floor', string='Floor')
    asset_id = fields.Many2one('estate.asset', string='Asset (optional)')
    capacity_l = fields.Float(string='Tank Capacity (L)')
    tank_balance = fields.Float(string='Tank Balance (L)', compute='_compute_tank_balance', store=True)
    last_reading = fields.Float(string='Last Tank Reading (L)')
    last_reading_date = fields.Datetime(string='Last Reading Date')
    # one2manys
    refill_ids = fields.One2many('estate.dg.refill', 'dg_id', string='Refills')
    log_ids = fields.One2many('estate.dg.log', 'dg_id', string='Daily Logs')
    tank_capacity_id = fields.Many2one(
        'estate.tank.capacity.master',
        string="Tank Capacity",
        required=True
    )

    # computed fields for monthly consumption (example)
    monthly_consumption = fields.Float(string='Monthly Consumption (L)', compute='_compute_monthly_consumption')

    refill_count = fields.Integer(
        string="Refills",
        compute="_compute_counts"
    )

    log_count = fields.Integer(
        string="Logs",
        compute="_compute_counts"
    )

    def _compute_counts(self):
        for rec in self:
            rec.refill_count = self.env['estate.dg.refill'].search_count([
                ('dg_id', '=', rec.id)
            ])
            rec.log_count = self.env['estate.dg.log'].search_count([
                ('dg_id', '=', rec.id)
            ])

    @api.onchange('generator_master_id')
    def _onchange_generator_master(self):
        if self.generator_master_id:
            self.name = self.generator_master_id.name
            self.code = self.generator_master_id.generator_code
            self.building_id = self.generator_master_id.building_id
            self.unit_id = self.generator_master_id.unit_id
            self.floor_id = self.generator_master_id.floor_id
        else:
            self.name = False
            self.code = False
            self.building_id = False
            self.unit_id = False
            self.floor_id = False

    @api.depends('refill_ids')
    def _compute_tank_balance(self):
        for rec in self:
            # tank balance = last known reading + net refills after last reading (best-effort)
            # Simpler approach: sum of refills - consumption recorded via logs (we'll compute using logs)
            total_refill = sum(rec.refill_ids.mapped('liters'))
            total_consumed = sum(rec.log_ids.mapped('consumed_liters'))
            rec.tank_balance = (rec.last_reading or 0.0) + total_refill - total_consumed

    def _compute_monthly_consumption(self):
        from datetime import datetime, timedelta
        now = fields.Date.context_today(self)
        start = (fields.Date.to_date(now).replace(day=1))
        for rec in self:
            logs = rec.env['estate.dg.log'].search([('dg_id', '=', rec.id), ('date', '>=', start)])
            rec.monthly_consumption = sum(logs.mapped('consumed_liters'))

    def action_open_refills(self):
        return {
            'name': 'Refills',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.dg.refill',
            'domain': [('dg_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {
                'default_dg_id': self.id,
            }
        }

    def action_open_logs(self):
        return {
            'name': 'DG Logs',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.dg.log',
            'domain': [('dg_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {
                'default_dg_id': self.id,
            }
        }




class ResUsers(models.Model):
    _inherit = 'res.users'

    dg_parent_id = fields.Many2one('res.users', string="DG Manager")
    dg_child_ids = fields.One2many('res.users', 'dg_parent_id', string="DG Subordinates")