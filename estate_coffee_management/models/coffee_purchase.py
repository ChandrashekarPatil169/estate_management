from odoo import models, fields, api
from odoo.exceptions import UserError


class CoffeePurchase(models.Model):
    _name = "coffee.purchase"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Coffee Purchase"
    _rec_name = "ingredient_master_id"
    _order = "id desc"

    ingredient_id = fields.Many2one(
        "coffee.ingredient.master",
        string="Ingredient",
        tracking=True,  # ✅ track changes in chatter
        ondelete='set null'
    )
    ingredient_master_id = fields.Many2one(
        "coffee.ingredient.master",
        string="Ingredient",
        tracking=True
    )

    quantity = fields.Float(
        string="Quantity",
        required=True,
        tracking=True  # ✅ track changes in chatter
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        required=True,
        tracking=True
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.today,
        tracking=True  # ✅ track changes in chatter
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('purchased', 'Purchased')
    ], default='draft', tracking=True)

    purchased_by_id = fields.Many2one(
        'res.partner',
        string="Purchased By",
        tracking=True
    )

    purchase_date = fields.Date(
        string="Purchase Date",
        default=fields.Date.today,
        tracking=True
    )

    purchase_cost = fields.Float(
        string="Purchase Cost",
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
    )

    @api.onchange('ingredient_master_id')
    def _onchange_ingredient_master_id(self):
        for rec in self:
            if rec.ingredient_master_id:
                rec.uom_id = rec.ingredient_master_id.uom_id.id
            else:
                rec.uom_id = False

    def action_confirm(self):
        for rec in self:

            if rec.quantity <= 0:
                raise UserError("Quantity must be greater than zero.")

            # Search main stock linked to master
            stock = self.env['estate.coffee.ingredient'].search([
                ('ingredient_master_id', '=', rec.ingredient_master_id.id)
            ], limit=1)

            # If not found → create stock record
            if not stock:
                stock = self.env['estate.coffee.ingredient'].create({
                    'ingredient_master_id': rec.ingredient_master_id.id,
                    'name': rec.ingredient_master_id.name,
                    'uom_id': rec.ingredient_master_id.uom_id.id,
                    'quantity': 0.0
                })

            # Increase main stock quantity
            stock.quantity += rec.quantity

            rec.state = 'purchased'


