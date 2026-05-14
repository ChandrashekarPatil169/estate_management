from odoo import models, fields, api


class CoffeeIngredientMaster(models.Model):
    _name = 'coffee.ingredient.master'
    _description = 'Coffee Ingredient Master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = "id desc"

    name = fields.Char(
        string="Ingredient Name",
        required=True
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
    )



    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for rec, vals in zip(records, vals_list):

            uom_id = vals.get('uom_id') or rec.uom_id.id

            stock = self.env['estate.coffee.ingredient'].search([
                ('ingredient_master_id', '=', rec.id)
            ], limit=1)

            if not stock:
                self.env['estate.coffee.ingredient'].create({
                    'ingredient_master_id': rec.id,
                    'name': rec.name,
                    'uom_id': uom_id,
                    'quantity': 0.0
                })

        return records


class CoffeeIngredient(models.Model):
    _name = 'estate.coffee.ingredient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Main Stock Ingredient'
    _rec_name = "name"
    _order = "id desc"

    name = fields.Char(
        string="Ingredient Name",
        required=True,
        tracking=True  # ✅ track changes in chatter
    )
    ingredient_master_id = fields.Many2one(
        'coffee.ingredient.master',
    )

    unit = fields.Selection(
        [('kg', 'Kg'), ('ltr', 'Liter'), ('pcs', 'Pieces')],
        string="Unit",
        tracking=True  # ✅ track when unit is changed
    )
    quantity = fields.Float(
        string="Quantity in Main Stock",
        default=0.0,
        tracking=True  # ✅ track quantity changes in chatter
    )

    # Link to purchases and building transfers (not tracked, just relations)
    purchase_ids = fields.One2many(
        'coffee.purchase',
        'ingredient_master_id',
        string="Purchases"
    )
    building_transfer_ids = fields.One2many(
        'coffee.building.transfer',
        'ingredient_id',
        string="Transfers to Building"
    )
    purchase_count = fields.Integer(compute="_compute_counts")
    transfer_count = fields.Integer(compute="_compute_counts")
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        tracking=True
    )

    @api.depends('ingredient_master_id')
    def _compute_counts(self):
        for rec in self:
            if rec.ingredient_master_id:
                rec.purchase_count = self.env['coffee.purchase'].search_count([
                    ('ingredient_master_id', '=', rec.ingredient_master_id.id)
                ])
            else:
                rec.purchase_count = 0

            rec.transfer_count = self.env['coffee.building.transfer'].search_count([
                ('ingredient_id', '=', rec.id)
            ])

    def action_view_purchases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchases',
            'res_model': 'coffee.purchase',
            'view_mode': 'list,form',
            'domain': [
                ('ingredient_master_id', '=', self.ingredient_master_id.id)
            ],
            'context': {
                'default_ingredient_master_id': self.ingredient_master_id.id,
            }
        }

    def action_view_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'res_model': 'coffee.building.transfer',
            'view_mode': 'list,form',
            'domain': [('ingredient_id', '=', self.id)],
            'context': {
                'default_ingredient_id': self.id,
            }
        }

    def add_stock(self, amount):
        """Add stock to main ingredient."""
        self.quantity += amount
