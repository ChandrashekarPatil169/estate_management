from odoo import models, fields, api
from odoo.exceptions import UserError

class MachineStock(models.Model):
    _name = 'machine.stock'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Machine Stock / Refill Record'
    _rec_name = 'machine_id'
    _order = "id desc"

    machine_id = fields.Many2one(
        'coffee.machine', string="Machine", required=True
    )
    building_id = fields.Many2one(
        related='machine_id.building_id', string="Building", store=True, readonly=True
    )
    building_id_main = fields.Many2one("estate.building",
        string="Building", store=True
    )
    building_stock_id = fields.Many2one(
        'building.stock',
        string="Building Stock",
        ondelete="cascade"
    )
    ingredient_id = fields.Many2one(
        'estate.coffee.ingredient', string="Ingredient", required=True
    )
    quantity = fields.Float(string="Quantity in Machine", default=0.0)
    refill_date = fields.Datetime(string="Refill Date", default=fields.Datetime.now)
    employee_id = fields.Many2one('hr.employee', string="Refilled By")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft', tracking=True)
    allowed_machine_ids = fields.Many2many(
        'coffee.machine',
        compute='_compute_allowed_machines',
        store=True
    )

    @api.depends('building_id_main')
    def _compute_allowed_machines(self):
        for rec in self:
            if rec.building_id_main:
                stocks = self.env['building.stock'].search([
                    ('building_id', '=', rec.building_id_main.id)
                ])
                rec.allowed_machine_ids = stocks.mapped('allowed_machine_ids')
            else:
                rec.allowed_machine_ids = [(5, 0, 0)]

    @api.onchange('quantity', 'building_stock_id')
    def _onchange_quantity(self):
        if self.building_stock_id and self.quantity:

            available_qty = sum(
                self.env['coffee.building.transfer'].search([
                    ('building_stock_id', '=', self.building_stock_id.id)
                ]).mapped('amount')
            )

            if self.quantity > available_qty:
                raise UserError(
                    f"Available stock: {available_qty}"
                )

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    @api.model
    def fill_machine(self, machine_id, ingredient_id, amount, employee_id):
        """
        Refill a coffee machine from building stock (programmatic API).
        This will create a negative transfer and then create the machine.stock row.
        """
        machine = self.env['coffee.machine'].browse(machine_id)
        if not machine:
            raise UserError("Machine not found.")

        building_stock = self.env['building.stock'].search([
            ('building_id', '=', machine.building_id.id),
            ('ingredient_id', '=', ingredient_id)
        ], limit=1)

        if not building_stock:
            raise UserError("No stock for this ingredient in building!")

        if building_stock.quantity < amount:
            raise UserError("Not enough stock in building!")

        # Create the negative transfer (deduct building stock)
        self.env['coffee.building.transfer'].create({
            'building_stock_id': building_stock.id,
            'building_id': machine.building_id.id,
            'ingredient_id': ingredient_id,
            'amount': -amount,
            'employee_id': employee_id
        })

        # Create machine refill record but tell create() not to create the transfer again
        return self.with_context(already_deducted=True).create({
            'machine_id': machine.id,
            'ingredient_id': ingredient_id,
            'quantity': amount,
            'employee_id': employee_id,
            'building_stock_id': building_stock.id,
        })

    def action_confirm(self):
        for rec in self:

            if rec.state == 'confirmed':
                continue

            if rec.quantity <= 0:
                raise UserError("Refill quantity must be greater than zero.")

            building_stock = rec.building_stock_id

            if not building_stock:
                raise UserError("Building stock not found.")

            # Always calculate latest confirmed stock
            available_qty = sum(
                self.env['coffee.building.transfer'].search([
                    ('building_stock_id', '=', building_stock.id),
                    ('state', '=', 'confirmed')
                ]).mapped('amount')
            )

            if rec.quantity > available_qty:
                raise UserError(
                    f"Not enough stock in building.\n"
                    f"Available: {available_qty}\n"
                    f"Requested: {rec.quantity}"
                )

            # Create negative confirmed transfer
            self.env['coffee.building.transfer'].create({
                'building_stock_id': building_stock.id,
                'building_id': building_stock.building_id.id,
                'ingredient_id': building_stock.ingredient_id.id,
                'amount': -rec.quantity,
                'employee_id': rec.employee_id.id,
                'state': 'confirmed'
            })

            rec.state = 'confirmed'

