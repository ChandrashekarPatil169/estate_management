from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta  # fixed import


class EstateDGLog(models.Model):
    _name = 'estate.dg.log'
    _description = 'DG Daily Log'
    _order = 'date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    dg_id = fields.Many2one('estate.dg', string='DG', required=True)
    date = fields.Date(string='Date', required=True)
    session = fields.Selection([('morning', 'Morning'), ('evening', 'Evening')], required=True)
    time = fields.Float(string='Time (hour)', help='Time of entry as decimal hours (optional)')
    reading = fields.Float(string='Tank Reading (L)', required=True)
    topup_liters = fields.Float(string='Top-up (L)', default=0.0)
    running_hours = fields.Float(string='DG Running Hours', default=0.0)
    operator = fields.Many2one('hr.employee', string='Operator')
    operator_name = fields.Char(string='Additional Operator')
    remarks = fields.Text(string='Remarks')

    consumed_liters = fields.Float(string='Consumed (L)', compute='_compute_consumption', store=True)
    linked_refill_ids = fields.Many2many('estate.dg.refill', compute='_compute_linked_refills')
    from_datetime = fields.Datetime(string="From Date & Time")
    to_datetime = fields.Datetime(string="To Date & Time")

    running_hours_main = fields.Float(
        string="DG Running Hours",
        compute="_compute_running_hours_main",
        store=True
    )

    _sql_constraints = [
        ('dg_date_session_unique', 'unique(dg_id, date, session)',
         'You can only have one log per DG per date per session (morning/evening).')
    ]

    @api.depends('from_datetime', 'to_datetime')
    def _compute_running_hours_main(self):
        for rec in self:
            rec.running_hours_main = 0.0

            if rec.from_datetime and rec.to_datetime:
                if rec.to_datetime < rec.from_datetime:
                    raise ValidationError(
                        "To Date & Time cannot be before From Date & Time."
                    )

                delta = rec.to_datetime - rec.from_datetime
                rec.running_hours_main = delta.total_seconds() / 3600.0

    def _compute_linked_refills(self):
        for rec in self:
            start_datetime = datetime.combine(rec.date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            rec.linked_refill_ids = self.env['estate.dg.refill'].search([
                ('dg_id', '=', rec.dg_id.id),
                ('date', '>=', start_datetime),
                ('date', '<', end_datetime)
            ])

    @api.depends('dg_id', 'date', 'session', 'reading', 'topup_liters')
    def _compute_consumption(self):
        for rec in self:
            rec.consumed_liters = 0.0
            if rec.session != 'evening':
                continue

            # Find morning reading same day
            morning = self.search([
                ('dg_id', '=', rec.dg_id.id),
                ('date', '=', rec.date),
                ('session', '=', 'morning')
            ], limit=1)

            if morning:
                start_reading = morning.reading + (morning.topup_liters or 0.0)
            else:
                # fallback to last evening or last DG reading
                prev = self.search([
                    ('dg_id', '=', rec.dg_id.id),
                    ('date', '<', rec.date)
                ], order='date desc', limit=1)
                start_reading = prev.reading if prev else (rec.dg_id.last_reading or 0.0)

            # Sum refills on same day
            start_datetime = datetime.combine(rec.date, datetime.min.time())
            end_datetime = start_datetime + timedelta(days=1)
            refills = self.env['estate.dg.refill'].search([
                ('dg_id', '=', rec.dg_id.id),
                ('date', '>=', start_datetime),
                ('date', '<', end_datetime)
            ])
            refill_total = sum(r.liters or 0.0 for r in refills)

            # Calculate consumption
            consumed = (start_reading + refill_total) - rec.reading
            rec.consumed_liters = max(consumed, 0.0)  # avoid negative consumption

            # Update DG last reading
            rec.dg_id.last_reading = rec.reading
            rec.dg_id.last_reading_date = fields.Datetime.now()
