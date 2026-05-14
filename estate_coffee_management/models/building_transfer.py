# models/building_transfer.py
from odoo import models, fields, api
from odoo.exceptions import UserError


class CoffeeBuildingTransfer(models.Model):
    _name = 'coffee.building.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Building Stock Transfer / Refill'
    _rec_name = "building_id"
    _order = "id desc"

    building_stock_id = fields.Many2one(
        'building.stock',
        string="Building Stock",
        required=False,  # auto-resolved if missing
        ondelete='cascade',
        tracking=True
    )
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
    amount = fields.Float(
        string="Quantity",
        required=True,
        tracking=True
    )
    date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ], default='draft', tracking=True)

    uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        tracking=True
    )

    # ✅ Auto-fill defaults when created from Building Stock form/tab
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self._context.get("active_model") == "building.stock" and self._context.get("active_id"):
            stock = self.env["building.stock"].browse(self._context["active_id"])
            if stock:
                res["building_stock_id"] = stock.id
                res["building_id"] = stock.building_id.id
                res["ingredient_id"] = stock.ingredient_id.id
        return res




    @api.model_create_multi
    def create(self, vals_list):
        """ Ensure building_stock_id, building_id, and ingredient_id are always consistent """

        for vals in vals_list:
            stock = False

            # If building_stock_id is given, always set building_id & ingredient_id
            if vals.get("building_stock_id"):
                stock = self.env["building.stock"].browse(vals["building_stock_id"])
                if stock:
                    vals["building_id"] = stock.building_id.id
                    vals["ingredient_id"] = stock.ingredient_id.id

            # If only building_id + ingredient_id given, find/create stock
            if vals.get("building_id") and vals.get("ingredient_id") and not vals.get("building_stock_id"):
                stock = self.env["building.stock"].search([
                    ("building_id", "=", vals["building_id"]),
                    ("ingredient_id", "=", vals["ingredient_id"])
                ], limit=1)

                if not stock:
                    stock = self.env["building.stock"].create({
                        "building_id": vals["building_id"],
                        "ingredient_id": vals["ingredient_id"]
                    })

                vals["building_stock_id"] = stock.id

        records = super().create(vals_list)

        return records

    def action_confirm(self):
        for rec in self:

            if rec.state == 'confirmed':
                continue

            if rec.amount <= 0:
                raise UserError("Transfer quantity must be greater than zero.")

            ingredient = rec.ingredient_id

            if ingredient.quantity < rec.amount:
                raise UserError(
                    f"Not enough stock in Main Store.\n"
                    f"Available: {ingredient.quantity}"
                )

            # Deduct main stock
            ingredient.quantity -= rec.amount

            rec.state = 'confirmed'
