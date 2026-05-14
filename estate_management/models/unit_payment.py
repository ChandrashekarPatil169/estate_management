from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from markupsafe import Markup
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta

class EstatePaymentMethod(models.Model):
    _name = 'estate.payment.method'
    _description = 'Payment Method'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(
        string="Payment Method",
        required=True,tracking=True
    )
    active = fields.Boolean(default=True,tracking=True)



class EstateUnitPayment(models.Model):
    _name = 'estate.unit.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin', 'estate.payment.logic.mixin','delete.notification.mixin']
    _description = 'Unit Payment'
    _rec_name = 'name'
    _order = "id desc"

    # -------------------------
    # RELATIONS
    # -------------------------
    unit_id = fields.Many2one(
        'estate.unit',
        string="Unit",
        ondelete='cascade',
        required=True,
        tracking=True
    )

    payment_for_id = fields.Many2one(
        'estate.payment.type',
        string="Payment For",
        tracking=True
    )

    payment_for = fields.Char(
        related="payment_for_id.name",
        store=True,
        tracking=True
    )

    building_id = fields.Many2one(
        "estate.building",
        store=True,
        tracking=True,
        domain="[('property_id', '=', property_id)]"
    )
    property_id = fields.Many2one(
        'estate.property',
        string="Property",
        tracking=True
    )

    # -------------------------
    # PAYMENT DETAILS
    # -------------------------
    name = fields.Char(
        string="Payment Reference",
        copy=False,
        tracking=True
    )

    amount = fields.Float(string="Amount", tracking=True)
    payment_date = fields.Date(string="Payment Date", tracking=True)
    due_date = fields.Date(string="Due Date", tracking=True, required=True)

    meter_start_reading = fields.Float(string="Meter Start Reading", tracking=True)
    meter_end_reading = fields.Float(string="Meter End Reading", tracking=True)

    meter_consumed = fields.Float(
        string="Meter Consumed",
        compute="_compute_meter_amount",
        store=True,
        tracking=True
    )
    # 🔥 PAYMENT FOR → PRODUCT
    product_id = fields.Many2one(
        'product.template',
        string="Payment For",
        required=True,
        tracking=True
    )
    payment_done_date = fields.Date(
        string="Date of Payment",
        tracking=True
    )

    payment_method_id = fields.Many2one(
        'estate.payment.method',
        string="Payment Method",
        tracking=True
    )

    receipt_number = fields.Char(
        string="Receipt Number",
        tracking=True
    )

    # recurring payments

    recurring_payment = fields.Boolean(
        string="Recurring Payment",
        tracking=True
    )

    recurring_start_date = fields.Date(
        string="Recurring Start Date",
        tracking=True
    )

    recurring_end_date = fields.Date(
        string="Recurring End Date",
        tracking=True
    )

    amount_doubled = fields.Boolean(
        string="Amount Doubled",
        default=False,tracking=True
    )

    base_amount = fields.Float("Base Amount",tracking=True)

    amount_locked = fields.Boolean(
        string="Lock Amount",tracking=True
    )

    due_date_locked = fields.Boolean(
        string="Lock Due Date",tracking=True
    )
    description = fields.Char(
        string="Description",
        tracking=True
    )

    service_billing_date = fields.Date(
        string="Service / Billing Date",
        tracking=True
    )

    # -------------------------
    # CONSTRAINT
    # -------------------------
    _sql_constraints = [
        (
            'unique_unit_payment_per_month',
            'unique(unit_id, payment_for_id, due_date)',
            'Payment already exists for this unit, fund, and month.'
        )
    ]


    @api.constrains('payment_done_date', 'receipt_number')
    def _check_receipt_on_payment(self):
        for rec in self:
            if rec.payment_done_date and not rec.receipt_number:
                raise ValidationError(
                    _("Receipt Number is required when payment is completed.")
                )

    @api.onchange('product_id')
    def _onchange_product_id_set_amount(self):
        for rec in self:
            if rec.product_id and not rec.amount_locked:
                rec.amount = rec.product_id.list_price
                rec.base_amount = rec.product_id.list_price

    # @api.depends('meter_start_reading', 'meter_end_reading', 'product_id')
    # def _compute_meter_amount(self):
    #     for rec in self:
    #
    #         if rec.meter_start_reading and rec.meter_end_reading and rec.product_id:
    #
    #             units = rec.meter_end_reading - rec.meter_start_reading
    #             rec.meter_consumed = units
    #             rec.amount = units * rec.product_id.list_price
    #
    #         else:
    #             rec.meter_consumed = 0.0

    # @api.depends('meter_start_reading', 'meter_end_reading', 'product_id')
    # def _compute_meter_amount(self):
    #     for rec in self:
    #         if (
    #                 rec.meter_start_reading is not None
    #                 and rec.meter_end_reading is not None
    #                 and rec.product_id
    #         ):
    #             units = rec.meter_end_reading - rec.meter_start_reading
    #             rec.meter_consumed = units * rec.product_id.list_price
    #             rec.amount = rec.meter_consumed
    #         else:
    #             rec.meter_consumed = 0.0
    #             rec.amount = 0.0

    # -------------------------
    # CREATE
    # -------------------------
    def _check_and_double_amount(self):

        today = fields.Date.today()

        for rec in self:

            if (
                    rec.recurring_payment
                    and rec.due_date
                    and rec.due_date < today
                    and not rec.payment_done_date
            ):
                base_amount = rec.product_id.list_price

                rec.amount = rec.amount + base_amount

    # def _check_and_double_amount(self):
    #
    #     today = fields.Date.today()
    #
    #     for rec in self:
    #
    #         if (
    #                 rec.recurring_payment
    #                 and rec.due_date
    #                 and rec.due_date < today
    #                 and not rec.payment_done_date
    #                 and not rec.amount_doubled
    #         ):
    #             super(type(rec), rec).write({
    #                 'amount': rec.amount * 2,
    #                 'amount_doubled': True
    #             })

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # if vals.get('name'):
            #     raise ValidationError(_("Payment reference is auto-generated."))
            vals.pop('name', None)

            if not vals.get('due_date'):
                raise ValidationError(_("Due Date is required."))

            unit = self.env['estate.unit'].browse(vals['unit_id'])
            building_rec = self.env['estate.building'].browse(vals['building_id'])

            product = self.env['product.template'].browse(vals['product_id'])

            due_dt = fields.Date.from_string(vals['due_date'])
            month = due_dt.strftime('%m')
            year = due_dt.strftime('%Y')
            building_code = getattr(building_rec, 'building_code', building_rec.building_code)
            unit_code = getattr(unit, 'unit_code', unit.display_name)
            product_name = product.name.replace('/', '_')

            # vals['base_amount'] = vals.get('amount', 0)

            # ✅ FINAL PREFIX FORMAT
            vals['name'] = (
                f"{building_code}/"
                f"{unit_code}/"
                f"{year}/"
                f"{month}/"
                f"{product_name}"
            )

        records = super().create(vals_list)

        for rec in records:
            if not rec.base_amount:
                rec.base_amount = rec.amount

        records._check_and_double_amount()

        # records = super().create(vals_list)
        #
        # records._check_and_double_amount()

        for record in records:
            record.message_post(
                body=Markup(
                    _("Payment created:<br/><b>%s</b>") % record.name
                )
            )

        return records

    def write(self, vals):

        today = fields.Date.today()

        for rec in self:

            # RUN LOGIC ONLY IF THESE FIELDS CHANGE
            if 'due_date' in vals or 'recurring_payment' in vals:

                due_date = vals.get('due_date', rec.due_date)

                if isinstance(due_date, str):
                    due_date = fields.Date.from_string(due_date)

                recurring = vals.get('recurring_payment', rec.recurring_payment)
                payment_done = vals.get('payment_done_date', rec.payment_done_date)

                if (
                        recurring
                        and due_date
                        and due_date < today
                        and not payment_done
                ):
                    base_amount = rec.base_amount
                    vals['amount'] = rec.amount + base_amount

            # -------------------
            # NAME RECOMPUTE
            # -------------------
            if any(k in vals for k in ('building_id', 'unit_id', 'due_date', 'product_id')):
                unit = self.env['estate.unit'].browse(vals.get('unit_id', rec.unit_id.id))
                building_rec = self.env['estate.building'].browse(vals.get('building_id', rec.building_id.id))
                product = self.env['product.template'].browse(vals.get('product_id', rec.product_id.id))

                due_dt = fields.Date.from_string(vals.get('due_date', rec.due_date))
                month = due_dt.strftime('%m')
                year = due_dt.strftime('%Y')

                building_code = getattr(building_rec, 'building_code', building_rec.building_code)
                unit_code = getattr(unit, 'unit_code', unit.display_name)
                product_name = product.name.replace('/', '_')

                vals['name'] = f"{building_code}/{unit_code}/{year}/{month}/{product_name}"

        return super().write(vals)

    @api.onchange('amount_locked')
    def _restore_amount_when_locked(self):
        if self.amount_locked and not self.amount and self.base_amount:
            self.amount = self.base_amount

    @api.onchange('due_date_locked')
    def _restore_due_date_when_locked(self):
        if self.due_date_locked and not self.due_date:
            self.due_date = fields.Date.today()

    # def write(self, vals):
    #     for rec in self:
    #
    #         # Only recompute name if relevant fields changed
    #         if any(k in vals for k in ('building_id', 'unit_id', 'due_date', 'product_id')):
    #             unit = self.env['estate.unit'].browse(
    #                 vals.get('unit_id', rec.unit_id.id)
    #             )
    #
    #             building_rec = self.env['estate.building'].browse(
    #                 vals.get('building_id', rec.building_id.id)
    #             )
    #
    #             product = self.env['product.template'].browse(
    #                 vals.get('product_id', rec.product_id.id)
    #             )
    #
    #             due_date = vals.get('due_date', rec.due_date)
    #             due_dt = fields.Date.from_string(due_date)
    #
    #             month = due_dt.strftime('%m')
    #             year = due_dt.strftime('%Y')
    #
    #             building_code = getattr(
    #                 building_rec, 'building_code', building_rec.building_code
    #             )
    #             unit_code = getattr(unit, 'unit_code', unit.display_name)
    #             product_name = product.name.replace('/', '_')
    #
    #             vals['name'] = (
    #                 f"{building_code}/"
    #                 f"{unit_code}/"
    #                 f"{year}/"
    #                 f"{month}/"
    #                 f"{product_name}"
    #             )
    #
    #     res = super().write(vals)
    #
    #     self._check_and_double_amount()
    #
    #     return res

        # return super().write(vals)
        #
        # self._check_and_double_amount()
        #
        # return res

    # -------------------------
    # COMPUTE
    # -------------------------
    @api.onchange('payment_done_date')
    def _handle_recurring_payment(self):

        today = fields.Date.today()

        for rec in self:

            # ✅ RESET AMOUNT WHEN PAYMENT DONE
            if rec.payment_done_date and rec.product_id:
                rec.amount = rec.product_id.list_price
                rec.base_amount = rec.product_id.list_price

            if rec.recurring_payment and rec.payment_done_date:

                rec.recurring_start_date = today
                rec.recurring_end_date = today + relativedelta(years=1)

                if rec.due_date:
                    rec.due_date = rec.due_date + relativedelta(months=1)

                rec.amount_doubled = False

    @api.onchange('due_date', 'recurring_payment')
    def _onchange_due_date_recurring(self):

        today = fields.Date.today()

        for rec in self:

            if (
                    rec.recurring_payment
                    and rec.due_date
                    and rec.due_date < today
            ):
                # base_amount = rec.product_id.list_price
                base_amount = rec.base_amount

                rec.amount = rec.amount + base_amount

    @api.depends('meter_start_reading', 'meter_end_reading')
    def _compute_meter_consumed(self):
        for rec in self:
            rec.meter_consumed = (
                rec.meter_end_reading - rec.meter_start_reading
                if rec.meter_end_reading and rec.meter_start_reading
                else 0.0
            )

    @api.depends('meter_start_reading', 'meter_end_reading', 'product_id')
    def _compute_meter_amount(self):
        for rec in self:

            if (
                    rec.meter_start_reading > 0
                    and rec.meter_end_reading > 0
                    and rec.product_id
            ):

                units = rec.meter_end_reading - rec.meter_start_reading
                rec.meter_consumed = units
                rec.amount = units * rec.product_id.list_price

            else:
                rec.meter_consumed = 0.0

    # @api.depends('meter_start_reading', 'meter_end_reading', 'product_id')
    # def _compute_meter_amount(self):
    #     for rec in self:
    #         if (
    #                 rec.meter_start_reading is not None
    #                 and rec.meter_end_reading is not None
    #                 and rec.product_id
    #         ):
    #             units = rec.meter_end_reading - rec.meter_start_reading
    #             rec.meter_consumed = units * rec.product_id.list_price
    #             rec.amount = rec.meter_consumed
    #         else:
    #             rec.meter_consumed = 0.0
    #             # rec.amount = 0.0

    # -------------------------
    # REMINDER
    # -------------------------
    @api.model
    def _send_due_payment_reminders(self):
        today = date.today()
        upcoming = today + timedelta(days=1)

        due_payments = self.search([
            ('recurring_payment', '=', True),
            ('due_date', '<=', upcoming),
            ('due_date', '>=', today - timedelta(days=7)),
        ])

        template = self.env.ref(
            'estate_management.email_template_due_payment_reminder',
            raise_if_not_found=False
        )

        if not template:
            return

        for payment in due_payments:
            template.send_mail(payment.id, force_send=True)

    @api.model
    def cron_unit_payment_due_reminder(self):

        today = fields.Date.today()

        payments = self.search([
            ('due_date', '!=', False),
            ('payment_done_date', '=', False)
        ])

        Mail = self.env['mail.mail']

        for payment in payments:

            if payment.payment_done_date:
                continue

            payment._check_and_double_amount()

            days_left = (payment.due_date - today).days

            if days_left in [15, 7, 1]:
                body = f"""
                <p><b>Unit Payment Due Reminder</b></p>

                <p>This is a reminder that a unit payment is approaching its due date.</p>

                <table border="0" cellpadding="4" cellspacing="0">
                <tr>
                    <td><b>Unit</b></td>
                    <td>: {payment.unit_id.name}</td>
                </tr>
                <tr>
                    <td><b>Building</b></td>
                    <td>: {payment.building_id.name}</td>
                </tr>
                <tr>
                    <td><b>Property</b></td>
                    <td>: {payment.property_id.name or '-'}</td>
                </tr>
                <tr>
                    <td><b>Payment For</b></td>
                    <td>: {payment.product_id.name}</td>
                </tr>
                <tr>
                    <td><b>Amount</b></td>
                    <td>: {payment.amount}</td>
                </tr>
                <tr>
                    <td><b>Due Date</b></td>
                    <td>: {payment.due_date}</td>
                </tr>
                <tr>
                    <td><b>Days Remaining</b></td>
                    <td>: {days_left}</td>
                </tr>
                </table>

                <br/>

                <p>Please ensure the payment is completed before the due date.</p>

                <p>
                Regards,<br/>
                <b>{self.env.company.name}</b>
                </p>
                """

                payment.message_post(
                    body=Markup(body),
                    subject="Unit Payment Due Reminder",
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment"
                )

                # SEND EMAIL (same pattern as CRM)
                for partner in payment.message_partner_ids:
                    if partner.email:
                        Mail.create({
                            'subject': "Unit Payment Due Reminder",
                            'body_html': body,
                            'email_to': partner.email,
                            'email_from': self.env.company.email,
                            'auto_delete': False,
                        })

            # -------------------------
            # AFTER DUE DATE (EVERY DAY)
            # -------------------------
            elif days_left < 0:

                overdue_days = abs(days_left)

                body = f"""
                <p><b>Overdue Payment Alert</b></p>

                <p>This is to inform you that the following payment is overdue.</p>

                <table border="0" cellpadding="4" cellspacing="0">
                <tr>
                    <td><b>Building</b></td>
                    <td>: {payment.building_id.name}</td>
                </tr>
                <tr>
                    <td><b>Property</b></td>
                    <td>: {payment.property_id.name or '-'}</td>
                </tr>
                <tr>
                    <td><b>Payment For</b></td>
                    <td>: {payment.product_id.name}</td>
                </tr>
                <tr>
                    <td><b>Amount Due</b></td>
                    <td>: {payment.amount}</td>
                </tr>
                <tr>
                    <td><b>Due Date</b></td>
                    <td>: {payment.due_date}</td>
                </tr>
                <tr>
                    <td><b>Overdue By</b></td>
                    <td>: {overdue_days} days</td>
                </tr>
                </table>

                <br/>

                <p>Please arrange to settle the outstanding payment at the earliest.</p>

                <p>
                Regards,<br/>
                <b>{self.env.company.name}</b>
                </p>
                """

                payment.message_post(
                    body=Markup(body),
                    subject="Overdue Payment Reminder",
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment"
                )

                # SEND EMAIL
                for partner in payment.message_partner_ids:
                    if partner.email:
                        Mail.create({
                            'subject': "Overdue Payment Reminder",
                            'body_html': body,
                            'email_to': partner.email,
                            'email_from': self.env.company.email,
                            'auto_delete': False,
                        })



    # def _check_and_double_amount(self):
    #
    #     today = fields.Date.today()
    #
    #     for rec in self:
    #
    #         if (
    #                 rec.recurring_payment
    #                 and rec.due_date
    #                 and rec.due_date < today
    #                 and not rec.payment_done_date
    #                 and not rec.amount_doubled
    #         ):
    #             rec.amount = rec.amount * 2
    #             rec.amount_doubled = True

    # @api.model
    # def _cron_unit_payment_reminder(self):
    #     today = fields.Date.today()
    #
    #     records = self.search([
    #         ('payment_done_date', '=', False),
    #         ('due_date', '!=', False),
    #     ])
    #
    #     template = self.env.ref(
    #         'estate_management.email_template_unit_payment_reminder',
    #         raise_if_not_found=False
    #     )
    #
    #     for rec in records:
    #
    #         if not rec.due_date:
    #             continue
    #
    #         days_remaining = (rec.due_date - today).days
    #
    #         # Get follower emails
    #         emails = rec.message_follower_ids.mapped('partner_id.email')
    #         emails = [email for email in emails if email]
    #
    #         if not emails:
    #             continue
    #
    #         # -----------------------------
    #         # 15 DAYS BEFORE
    #         # -----------------------------
    #         if days_remaining == 15 and template:
    #             template.send_mail(
    #                 rec.id,
    #                 force_send=True,
    #                 email_values={
    #                     'email_to': ','.join(emails)
    #                 }
    #             )
    #
    #         # -----------------------------
    #         # 7 DAYS BEFORE
    #         # -----------------------------
    #         elif days_remaining == 7 and template:
    #             template.send_mail(
    #                 rec.id,
    #                 force_send=True,
    #                 email_values={
    #                     'email_to': ','.join(emails)
    #                 }
    #             )
    #
    #         # -----------------------------
    #         # AFTER DUE DATE → DOUBLE
    #         # -----------------------------
    #         elif days_remaining < 0:
    #             original_amount = rec.product_id.list_price
    #
    #             if rec.amount < original_amount * 2:
    #                 rec.amount = original_amount * 2

    # @api.model
    # def _cron_unit_payment_reminder(self):
    #     today = fields.Date.today()
    #
    #     records = self.search([
    #         ('payment_done_date', '=', False),
    #         ('due_date', '!=', False),
    #     ])
    #
    #     template = self.env.ref(
    #         'estate_management.email_template_unit_payment_reminder',
    #         raise_if_not_found=False
    #     )
    #
    #     if not template:
    #         return
    #
    #     for rec in records:
    #
    #         if not rec.due_date:
    #             continue
    #
    #         days_remaining = (rec.due_date - today).days
    #
    #         # Only trigger on 15 or 7 days before
    #         if days_remaining not in (15, 7) and days_remaining >= 0:
    #             continue
    #
    #         # 🔥 SEND EMAIL PER FOLLOWER
    #         followers = rec.message_follower_ids.mapped('partner_id')
    #
    #         for partner in followers:
    #             if not partner.email:
    #                 continue
    #
    #             template.with_context(
    #                 recipient_name=partner.name
    #             ).send_mail(
    #                 rec.id,
    #                 force_send=True,
    #                 email_values={
    #                     'email_to': partner.email,
    #                 }
    #             )
    #
    #         # -----------------------------
    #         # AFTER DUE DATE → DOUBLE
    #         # -----------------------------
    #         if days_remaining < 0:
    #             original_amount = rec.product_id.list_price
    #
    #             if rec.amount < original_amount * 2:
    #                 rec.amount = original_amount * 2