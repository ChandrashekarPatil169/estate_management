from odoo import models, fields, api
from odoo.exceptions import UserError


class BuildingStock(models.Model):
    _name = 'building.stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Building Stock'
    _rec_name ="building_id"
    _order = "id desc"


    building_id = fields.Many2one(
        'estate.building',
        string="Building",
        required=True,
        tracking=True
    )
    ingredient_id = fields.Many2one(
        'estate.coffee.ingredient',
        string="Ingredient",
        required=True,
        tracking=True
    )

    # Quantity is computed based on transfers
    quantity = fields.Float(
        string="Quantity in Building Stock",
        compute='_compute_quantity',
        store=True,
        tracking=True
    )

    # Refills from Main Stock (positive transfers only)
    building_refill_ids = fields.One2many(
        'coffee.building.transfer',
        'building_stock_id',
        string="Main Stock Refills",
        domain=[('amount', '>', 0)],
        tracking=True,
    )

    # Machine refills linked via building_stock_id
    machine_refill_ids = fields.One2many(
        'machine.stock',
        'building_stock_id',
        string="Machine Refills",
        tracking=True
    )
    refill_count = fields.Integer(compute="_compute_refill_count")
    machine_refill_count = fields.Integer(compute="_compute_machine_count")
    allowed_machine_ids = fields.Many2many(
        'coffee.machine',
        'building_stock_machine_rel',
        'building_stock_id',
        'machine_id',
        string="Machines Available"
    )
    def _compute_refill_count(self):
        for rec in self:
            rec.refill_count = len(rec.building_refill_ids)
            rec.machine_refill_count = len(rec.machine_refill_ids)

    def action_view_refills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refills',
            'res_model': 'coffee.building.transfer',
            'view_mode': 'list,form',
            'domain': [('building_stock_id', '=', self.id)],
            'context': {
                'default_building_stock_id': self.id,
                'default_building_id': self.building_id.id,
                'default_ingredient_id': self.ingredient_id.id,
            }
        }

    def action_view_machine_refills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Machine Refills',
            'res_model': 'machine.stock',
            'view_mode': 'list,form',
            'domain': [('building_stock_id', '=', self.id)],
            'context': {
                'default_building_stock_id': self.id,
                'default_ingredient_id': self.ingredient_id.id,
                'default_machine_id': False,
                'default_building_id_main': self.building_id.id,
            }
        }
    @api.depends('building_refill_ids.amount')
    def _compute_quantity(self):
        """Compute building stock as sum of all transfers (positive additions, negative deductions)."""
        for stock in self:
            transfers = self.env['coffee.building.transfer'].search([
                ('building_stock_id', '=', stock.id)
            ])
            stock.quantity = sum(transfers.mapped('amount') or [0.0])

    def transfer_from_main(self, ingredient_id, building_id, amount, employee_id=False):
        """
        Transfer ingredients from main stock to building stock.
        Creates a transfer record which will update building stock and deduct main stock
        centrally in coffee.building.transfer.create().
        """
        ingredient = self.env['estate.coffee.ingredient'].browse(ingredient_id)
        if not ingredient:
            raise UserError("Ingredient not found!")

        # Get or create building stock record
        stock = self.search([
            ('building_id', '=', building_id),
            ('ingredient_id', '=', ingredient_id)
        ], limit=1)
        if not stock:
            stock = self.create({
                'building_id': building_id,
                'ingredient_id': ingredient_id,
            })

        # Create transfer record (deduction from main stock handled in transfer.create)
        self.env['coffee.building.transfer'].create({
            'building_stock_id': stock.id,
            'building_id': building_id,
            'ingredient_id': ingredient_id,
            'amount': amount,
            'employee_id': employee_id
        })
        return True






class ResUsers(models.Model):
    _inherit = 'res.users'

    coffee_parent_id = fields.Many2one('res.users', string="Coffee Manager")
    coffee_child_ids = fields.One2many('res.users', 'coffee_parent_id', string="Coffee Subordinates")
