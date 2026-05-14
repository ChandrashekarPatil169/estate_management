from odoo import models, fields, api
from odoo.exceptions import UserError

class EstateDGRefill(models.Model):
    _name = 'estate.dg.refill'
    _description = 'Refill: Main Stock → DG Tank'
    _order = 'date desc'
    _rec_name = "fuel_type_id"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference')
    date = fields.Datetime(string='Date', default=fields.Datetime.now,  )
    dg_id = fields.Many2one('estate.dg', string='DG',  )
    liters = fields.Float(string='Liters',  )
    purchase_invoice = fields.Many2one('estate.dg.purchase', string='Purchase/Invoice')
    user_id = fields.Many2one('res.users', string='Issued By', default=lambda self: self.env.user)
    note = fields.Text(string='Remarks')
    fuel_type_id = fields.Many2one(
        'estate.fuel.type',
        string="Fuel Type",
         
    )

    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm')],
        default='draft'
    )

    def action_confirm(self):
        for rec in self:
            if rec.state == 'confirm':
                continue

            stock = self.env['estate.stock.main'].search([
                ('fuel_type_id', '=', rec.fuel_type_id.id)
            ], limit=1)

            if not stock:
                raise UserError("No stock available for this fuel type!")

            # Check quantity
            if rec.liters > stock.quantity_available:
                raise UserError("Not enough stock available!")

            # Reduce stock
            stock.quantity_available -= rec.liters

            rec.state = 'confirm'

    def action_issue(self):
        for rec in self:
            # create ledger issue
            rec.env['estate.stock.main'].create({
                'date': rec.date.date(),
                'source': 'issue',
                'ref': rec.name or ('refill-%s' % rec.id),
                'liters_out': rec.liters,
                'refill_id': rec.id,
            })
            # create/update DG last_reading & track the refill in one place
            # (we do not modify log readings here; operator adds logs separately)
