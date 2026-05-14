from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from markupsafe import Markup
# import pgeocode
#
# nomi = pgeocode.Nominatim('in')  # India

class EstateBuildingPayment(models.Model):
    _name = 'estate.building.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin','estate.payment.logic.mixin','delete.notification.mixin']
    _description = 'Building Payment'
    _rec_name = 'name'
    _order = "id desc"

    # 🔗 LINK TO BUILDING
    building_id = fields.Many2one(
        'estate.building',
        string="Building",
        required=True,
        ondelete='cascade',
        tracking=True
    )

    property_id = fields.Many2one(
        'estate.property',
        string="Property",
        tracking=True
    )

    # 💰 PAYMENT DETAILS
    name = fields.Char(
        string="Payment Reference",
        copy=False,
        tracking=True
    )

    product_id = fields.Many2one(
        'product.template',
        string="Payment For",
        required=True,
        tracking=True
    )

    amount = fields.Float(string="Amount", tracking=True)
    due_date = fields.Date(string="Due Date", required=True, tracking=True)
    payment_date = fields.Date(string="Payment Date", tracking=True)

    receipt_number = fields.Char(string="Receipt Number", tracking=True)
    meter_start_reading = fields.Float(string="Meter Start Reading", tracking=True)
    meter_end_reading = fields.Float(string="Meter End Reading", tracking=True)

    meter_consumed = fields.Float(
        string="Meter Consumed",
        compute="_compute_meter_amount",
        store=True,
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

    # recurring payments

    recurring_payment = fields.Boolean(
        string="Recurring Payment",
        tracking=True
    )

    recurring_start_date = fields.Date(
        string="Start Date",
        tracking=True
    )

    recurring_end_date = fields.Date(
        string="End Date",
        tracking=True
    )

    amount_doubled = fields.Boolean(
        string="Amount Doubled",
        default=False,
        tracking=True
    )

    base_amount = fields.Float("Base Amount",tracking=True)

    amount_locked = fields.Boolean(
        string="Lock Amount",
        tracking=True
    )

    due_date_locked = fields.Boolean(
        string="Lock Due Date",
        tracking=True
    )
    description = fields.Char(
        string="Description",
        tracking=True
    )

    service_billing_date = fields.Date(
        string="Service / Billing Date",
        tracking=True
    )
    def _check_and_double_amount(self):

        today = fields.Date.today()

        for rec in self:

            if (
                    rec.recurring_payment
                    and rec.due_date
                    and rec.due_date < today
                    and not rec.payment_done_date
            ):
                rec.amount = rec.amount + rec.base_amount

    # def _check_and_double_amount(self):
    #     today = fields.Date.today()
    #
    #     for rec in self:
    #         if (
    #                 rec.recurring_payment
    #                 and rec.due_date
    #                 and rec.due_date < today
    #                 and not rec.payment_done_date
    #                 and not rec.amount_doubled
    #         ):
    #             rec.write({
    #                 'amount': rec.amount * 2,
    #                 'amount_doubled': True
    #             })

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
    # -------------------
    # AUTO GENERATE NAME
    # -------------------

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
                rec.amount = rec.amount + rec.base_amount

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # remove name if passed
            vals.pop('name', None)

            building = self.env['estate.building'].browse(vals['building_id'])
            product = self.env['product.template'].browse(vals['product_id'])

            due_dt = fields.Date.from_string(vals['due_date'])
            month = due_dt.strftime('%m')
            year = due_dt.strftime('%Y')

            building_code = building.building_code
            product_name = product.name.replace('/', '_')

            # 18/3/2026
            product = self.env['product.template'].browse(vals['product_id'])

            amount = vals.get('amount') or product.list_price

            vals['amount'] = amount
            vals['base_amount'] = amount

            # vals['base_amount'] = vals.get('amount', 0)

            vals['name'] = (
                f"{building_code}/"
                f"{year}/"
                f"{month}/"
                f"{product_name}"
            )

        records = super().create(vals_list)

        records._check_and_double_amount()

        return records

        # return super().create(vals_list)
        #
        # records._check_and_double_amount()
        #
        # return records

    @api.model
    def cron_payment_due_reminder(self):

        today = fields.Date.today()

        payments = self.search([
            ('due_date', '!=', False),
            ('payment_done_date', '=', False)
        ])

        Mail = self.env['mail.mail']

        for payment in payments:

            days_left = (payment.due_date - today).days

            if days_left in [15, 7, 1]:
                body = f"""
                <p><b>Payment Due Reminder</b></p>

                <p>This is a reminder that the following payment is approaching its due date.</p>

                <table border="0" cellpadding="4" cellspacing="0">
                <tr>
                    <td><b>Building</b></td>
                    <td>: {payment.building_id.name}</td>
                </tr>
                <tr>
                    <td><b>Property</b></td>
                    <td>: {payment.property_id.name}</td>
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

                <p>Please ensure that the payment is completed before the due date to avoid any delays.</p>

                <p>
                Regards,<br/>
                <b>{self.env.company.name}</b>
                </p>
                """

                payment.message_post(
                    body=Markup(body),
                    subject="Payment Due Reminder",
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

    def write(self, vals):

        today = fields.Date.today()

        for rec in self:

            # ONLY run logic if due_date or recurring_payment is being changed
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
                    vals['amount'] = rec.amount + rec.base_amount

        return super().write(vals)

    # 18/3/2026
    @api.onchange('product_id')
    def _onchange_product_id_set_amount(self):
        for rec in self:
            if rec.product_id:
                rec.amount = rec.product_id.list_price
                rec.base_amount = rec.product_id.list_price



                # if payment.partner_id.email:
                #     self.env['mail.mail'].create({
                #         'subject': 'Payment Due Reminder',
                #         'body_html': body,
                #         'email_to': payment.partner_id.email,
                #         'email_from': self.env.company.email,
                #     }).send()

    # @api.model
    # def cron_payment_due_reminder(self):
    #
    #     today = fields.Date.today()
    #
    #     payments = self.search([
    #         ('due_date', '!=', False),
    #         ('date_of_payment', '=', False)
    #     ])
    #
    #     for payment in payments:
    #
    #         days_left = (payment.due_date - today).days
    #
    #         if days_left in [15, 7, 1]:
    #
    #             body = f"""
    # Payment Due Reminder
    #
    # Building  : {payment.building_id.name}
    # Property  : {payment.property_id.name}
    #
    # Payment For : {payment.payment_for}
    # Amount      : {payment.amount}
    # Due Date    : {payment.due_date}
    #
    # Days Remaining : {days_left}
    #
    # Please complete the payment before the due date.
    #
    # Regards,
    # {self.env.company.name}
    # """
    #
    #             payment.message_post(
    #                 body=body,
    #                 subject="Payment Due Reminder",
    #                 subtype_xmlid="mail.mt_comment"
    #             )
    #
    #             if payment.partner_id.email:
    #                 self.env['mail.mail'].create({
    #                     'subject': 'Payment Due Reminder',
    #                     'body_html': body,
    #                     'email_to': payment.partner_id.email,
    #                     'email_from': self.env.company.email,
    #                 }).send()

    # @api.model
    # def _cron_building_payment_reminder(self):
    #     today = fields.Date.today()
    #
    #     records = self.search([
    #         ('payment_done_date', '=', False),
    #         ('due_date', '!=', False),
    #     ])
    #
    #     template = self.env.ref(
    #         'estate_management.email_template_building_payment_reminder',
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
    #         # ---------------------------------
    #         # 15 DAYS BEFORE
    #         # ---------------------------------
    #         if days_remaining == 15 and template:
    #             template.send_mail(
    #                 rec.id,
    #                 force_send=True,
    #                 email_values={
    #                     'email_to': ','.join(emails)
    #                 }
    #             )
    #
    #         # ---------------------------------
    #         # 7 DAYS BEFORE
    #         # ---------------------------------
    #         elif days_remaining == 7 and template:
    #             template.send_mail(
    #                 rec.id,
    #                 force_send=True,
    #                 email_values={
    #                     'email_to': ','.join(emails)
    #                 }
    #             )
    #
    #         # ---------------------------------
    #         # AFTER DUE DATE → DOUBLE
    #         # ---------------------------------
    #         elif days_remaining < 0:
    #             original_amount = rec.product_id.list_price
    #
    #             if rec.amount < original_amount * 2:
    #                 rec.amount = original_amount * 2


    # @api.model
    # def _cron_building_payment_reminder(self):
    #     today = fields.Date.today()
    #
    #     records = self.search([
    #         ('payment_done_date', '=', False),
    #         ('due_date', '!=', False),
    #     ])
    #
    #     template = self.env.ref(
    #         'estate_management.email_template_building_payment_reminder',
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
    #         # -----------------------------
    #         # SEND ONLY ON 15 OR 7 DAYS BEFORE
    #         # -----------------------------
    #         if days_remaining not in (15, 7) and days_remaining >= 0:
    #             continue
    #
    #         # 🔥 SEND PER FOLLOWER
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

class EstateBuilding(models.Model):
    _name = 'estate.building'
    _inherit = ['mail.thread','estate.hierarchy.mixin','delete.notification.mixin']
    _description = 'Building'
    _rec_name = 'name'
    _order = "id desc"


    # === Basic Info ===
    name = fields.Char(string="Building Name", required=True, tracking=True)
    property_id = fields.Many2one('estate.property', string="Property", tracking=True)
    construction_year = fields.Char(string="Construction Year", tracking=True)
    usage = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('mixed', 'Mixed')
    ], string="Usage", tracking=True)

    usage_id = fields.Many2one(
        'estate.property.usage',
        string="Usage",
        ondelete='cascade',
        tracking=True
    )
    location_id = fields.Many2one(
        'custom.location',
        tracking=True
    )
    map_url = fields.Html(
        related='location_id.map_url',
        string="Google Map",
        tracking=True
    )




    water_tank = fields.Char(string="Water Tank", tracking=True)
    # ✅ ADDED (CODE LOGIC)
    building_code = fields.Char(string="Building Code", tracking=True,required=True)
    building_code_locked = fields.Boolean(default=False,tracking=True)
    # === Meters & Charges ===
    electricity_meter = fields.Char(string="Electricity Meter", tracking=True)
    water_meter = fields.Char(string="Water Meter", tracking=True)
    maintenance_charges = fields.Float(string="Maintenance Charges", tracking=True)

    # === Relations ===
    floor_ids = fields.One2many('estate.floor', 'building_id', string="Floors", tracking=True)

    # === Computed Fields ===
    number_of_floors = fields.Integer(compute="_compute_counts", string="Number of Floors", tracking=True)
    number_of_units = fields.Integer(compute="_compute_counts", string="Number of Units", tracking=True)
    number_of_rooms = fields.Integer(compute="_compute_counts", string="Number of Rooms", tracking=True)
    employee_count = fields.Integer(compute="_compute_employee_count", store=True, string="Employees",tracking=True)
    # === Taxes & Meters (RELATED) ===
    # property_tax = fields.Integer(string="Property Tax", tracking=True)
    # land_tax = fields.Integer(string="Land Tax", tracking=True)
    # municipal_tax = fields.Integer(string="Municipal Tax", tracking=True)
    property_tax = fields.Char(string="Property Tax", tracking=True)
    land_tax = fields.Char(string="Land Tax", tracking=True)
    municipal_tax = fields.Char(string="Municipal Tax", tracking=True)
    gas_meter = fields.Char(string="Gas Meter", tracking=True)
    legal_document_ids = fields.Many2many(
        'ir.attachment',
        'estate_building_ir_attachment_rel',
        'building_id',
        'attachment_id',
        string="Building Documents",
        tracking=True
    )

    legal_document_count = fields.Integer(
        compute="_compute_legal_document_count",
        tracking=True
    )

    # 🔼 UPPER
    hup_property_id = fields.Many2one('estate.property', required=True,string="Property",tracking=True)


    # 🔽 DOWNER
    hdown_floor_ids = fields.Many2many('estate.floor',string="Floors",tracking=True)
    hdown_unit_ids = fields.Many2many('estate.unit',string="Units",tracking=True)
    hdown_room_ids = fields.Many2many('estate.room',string="Rooms",tracking=True)
    hdown_table_ids = fields.Many2many('estate.room.table',string="Tables",tracking=True)

    # 🔢 COUNTS
    hcount_floor = fields.Integer(compute='_compute_hcounts',string="Floors",tracking=True)
    hcount_unit = fields.Integer(compute='_compute_hcounts',string="Units",tracking=True)
    hcount_room = fields.Integer(compute='_compute_hcounts',string="Rooms",tracking=True)
    hcount_table = fields.Integer(compute='_compute_hcounts',string="Tables",tracking=True)
    building_payment_ids = fields.One2many(
        'estate.building.payment',
        'building_id',
        string="Building Payments"
        , tracking=True
    )

    building_payment_count = fields.Integer(
        compute="_compute_building_payment_count",
        string="Payments"
        , tracking=True
    )


    hup_location_id = fields.Many2one(
        'estate.location',
        required=True,
        string="Location"
        , tracking=True
    )
    hcount_location = fields.Integer(
        compute="_compute_location_count",
        string="Location"
        , tracking=True
    )
    building_number = fields.Char(string="Building Number", tracking=True)

    address = fields.Text(string="Address", tracking=True)
    city = fields.Char(string="City / Town / Village", tracking=True)
    state = fields.Char(string="State", tracking=True)
    pincode = fields.Char(string="Pincode", tracking=True)

    responsible_employee_id = fields.Many2one(
        'res.partner',
        string="Responsible Employee",
        tracking=True
    )

    # @api.onchange('pincode')
    # def _onchange_pincode(self):
    #     for rec in self:
    #         if rec.pincode and len(rec.pincode) == 6:
    #
    #             try:
    #                 location = nomi.query_postal_code(rec.pincode)
    #
    #                 # ✅ SAFE CHECK
    #                 if not location.empty and location.place_name:
    #
    #                     city = location.place_name
    #                     state = location.state_name
    #
    #                     rec.city = city.split(',')[0] if city else False
    #                     rec.state = state if state else False
    #
    #                 else:
    #                     rec.city = False
    #                     rec.state = False
    #
    #             except Exception:
    #                 rec.city = False
    #                 rec.state = False

    def action_open_custom_location(self):
        self.ensure_one()

        return {
            'name': 'Location',
            'type': 'ir.actions.act_window',
            'res_model': 'custom.location',
            'view_mode': 'form',
            'res_id': self.location_id.id,
            'target': 'current',

            # Show only this building's locations
            'domain': [('building_id', '=', self.id)],

            # Auto default values
            'context': {
                'default_building_id': self.id,
                'default_property_id': self.hup_property_id.id,
            }
        }




    @api.depends('hup_location_id')
    def _compute_location_count(self):
        for rec in self:
            rec.hcount_location = 1 if rec.hup_location_id else 0

    def haction_open_location(self):
        self.ensure_one()
        return {
            'name': 'Location',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.location',
            'view_mode': 'form',
            'res_id': self.hup_location_id.id,
        }

    @api.depends('building_payment_ids')
    def _compute_building_payment_count(self):
        for rec in self:
            rec.building_payment_count = len(rec.building_payment_ids)

    def action_open_building_payments(self):
        self.ensure_one()
        return {
            'name': 'Building Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.building.payment',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('building_id', '=', self.id)],
            'context': {
                'default_building_id': self.id,
                'default_property_id': self.hup_property_id.id,
            }
        }

    def haction_open_floors(self):
        return self._open_hdown(
            'Floors',
            'estate.floor',
            self.hdown_floor_ids,
            {
                'default_hup_building_id': self.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    def haction_open_units(self):
        return self._open_hdown(
            'Units',
            'estate.unit',
            self.hdown_unit_ids,
            {
                'default_hup_building_id': self.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    def haction_open_rooms(self):
        return self._open_hdown(
            'Rooms',
            'estate.room',
            self.hdown_room_ids,
            {
                'default_hup_building_id': self.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    def haction_open_tables(self):
        return self._open_hdown(
            'Tables',
            'estate.room.table',
            self.hdown_table_ids,
            {
                'default_hup_building_id': self.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    # --------------------------------------------------
    # HIERARCHY COUNTS (NEW LOGIC)
    # --------------------------------------------------
    @api.depends(
        'hdown_floor_ids',
        'hdown_unit_ids',
        'hdown_room_ids',
        'hdown_table_ids'
    )
    def _compute_hcounts(self):
        for r in self:
            r.hcount_floor = len(r.hdown_floor_ids)
            r.hcount_unit = len(r.hdown_unit_ids)
            r.hcount_room = len(r.hdown_room_ids)
            r.hcount_table = len(r.hdown_table_ids)

    @api.depends('legal_document_ids')
    def _compute_legal_document_count(self):
        for rec in self:
            rec.legal_document_count = len(rec.legal_document_ids)

    def action_open_legal_documents(self):
        self.ensure_one()
        return {
            'name': 'Building Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.legal_document_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }

    # def action_open_custom_location(self):
    #     self.ensure_one()
    #
    #     return {
    #         'name': 'Location',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'custom.location',
    #         'view_mode': 'form',
    #         'target': 'current',
    #
    #         # 🔥 If building already has location, open it
    #         'res_id': self.location_id.id if self.location_id else False,
    #
    #         # 🔥 Auto default values if creating new
    #         'context': {
    #             'default_building_id': self.id,
    #             'default_property_id': self.hup_property_id.id if self.hup_property_id else False,
    #         }
    #     }

    # === Compute Methods ===
    @api.depends('floor_ids', 'floor_ids.unit_ids', 'floor_ids.unit_ids.room_ids')
    def _compute_counts(self):
        for record in self:
            record.number_of_floors = len(record.floor_ids)
            record.number_of_units = sum(len(f.unit_ids) for f in record.floor_ids)
            record.number_of_rooms = sum(len(u.room_ids) for f in record.floor_ids for u in f.unit_ids)



    @api.model_create_multi
    def create(self, vals_list):
        records = super(EstateBuilding, self).create(vals_list)

        for record, vals in zip(records, vals_list):

            # 🔒 LOCK BUILDING CODE AFTER FIRST SAVE (SILENT)
            if vals.get('building_code'):
                record.with_context(tracking_disable=True).write({
                    'building_code_locked': True
                })

            # 🌳 ADD TO PARENT HIERARCHY
            if record.hup_property_id:
                record._add_to_parent(
                    record.hup_property_id,
                    'hdown_building_ids'
                )

            if record.hup_location_id:
                record._add_to_parent(
                    record.hup_location_id,
                    'hdown_building_ids'
                )

            # 🧾 CHATTER — ONLY FILLED FIELDS
            log_items = []

            for key, value in vals.items():
                field = record._fields.get(key)

                if not field:
                    continue

                if field.type in ('one2many', 'many2many', 'html', 'binary'):
                    continue

                if value in (False, None, '', []):
                    continue

                display_value = value

                if field.type == 'many2one' and isinstance(value, int):
                    display_value = record.env[field.comodel_name].browse(value).display_name

                log_items.append(Markup("<b>%s</b>: %s") % (field.string, display_value))

            if log_items:
                record.message_post(
                    body=Markup("Building created with values:<br/>%s") %
                         Markup("<br/>").join(log_items)
                )

            # log_items = []
            # for key, value in vals.items():
            #     field = record._fields.get(key)
            #
            #     # Skip invalid or unwanted fields
            #     if not field:
            #         continue
            #     if field.type in ('one2many', 'many2many', 'html', 'binary'):
            #         continue
            #     if value in (False, None, '', []):
            #         continue  # 🔥 THIS IS THE KEY LINE
            #
            #     display_value = value
            #
            #     # Many2one → show name instead of ID
            #     if field.type == 'many2one' and isinstance(value, int):
            #         display_value = record.env[field.comodel_name].browse(value).display_name
            #
            #     log_items.append(f"<b>{field.string}</b>: {display_value}")
            #
            # if log_items:
            #     record.message_post(
            #         body=Markup(
            #             _("Building created with values:<br/>%s")
            #             % "<br/>".join(log_items)
            #         )
            #     )

        return records

    def write(self, vals):

        # ❌ BLOCK CODE CHANGE AFTER SAVE
        if 'building_code' in vals:
            for rec in self:
                if rec.building_code_locked:
                    raise ValidationError(
                        _("Building Code cannot be changed once saved.")
                    )

        changes_dict = {}
        for record in self:
            changes = []
            for field, new_value in vals.items():

                # 🚫 DO NOT LOG SYSTEM FIELDS
                if field in ('building_code_locked',):
                    continue

                if isinstance(new_value, (list, tuple)):
                    continue

                old_value = record[field]
                if old_value != new_value:
                    old_display = (
                        old_value.display_name
                        if hasattr(old_value, 'display_name')
                        else old_value
                    )
                    field_label = record._fields[field].string
                    changes.append(
                        f"<b>{field_label}</b>: {old_display} → {new_value}"
                    )

            if changes:
                changes_dict[record.id] = "<br/>".join(changes)

        res = super(EstateBuilding, self).write(vals)

        for record in self:
            if record.id in changes_dict:
                record.message_post(
                    body=Markup(_("Updated fields:<br/>%s") % changes_dict[record.id])
                )

        return res

