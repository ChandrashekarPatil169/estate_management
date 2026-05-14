from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from markupsafe import Markup
# import pgeocode
#
# nomi = pgeocode.Nominatim('in')  # India

class EstateUnitType(models.Model):
    _name = 'estate.unit.type'
    _description = 'Unit Type Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin','delete.notification.mixin']

    name = fields.Char(string="Unit Type", required=True,tracking=True)
    code = fields.Char(string="Code",tracking=True)
    active = fields.Boolean(default=True,tracking=True)


class EstateUnit(models.Model):
    _name = 'estate.unit'
    _inherit = ['mail.thread','mail.activity.mixin', 'estate.hierarchy.mixin', 'estate.security.mixin']
    _description = 'Unit'
    _rec_name = 'name'
    _order = "id desc"

    # 🔹 Basic Info
    name = fields.Char(string="Unit Name", required=True, tracking=True)

    # ✅ ADDED (CODE LOGIC)
    unit_code = fields.Char(string="Unit Code", tracking=True,required=True)
    unit_code_locked = fields.Boolean(default=False,tracking=True)

    unit_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial')
    ], string="Unit Type", tracking=True)
    unit_type_id = fields.Many2one(
        'estate.unit.type',
        string="Unit Type",
        tracking=True,
    )

    area_sqft = fields.Float(string="Area (sq.ft)", tracking=True)
    occupancy_status = fields.Selection([
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied')
    ], string="Occupancy Status", tracking=True)
    tenant = fields.Char(string="Tenant", tracking=True)
    lease_start = fields.Date(string="Lease Start", tracking=True)
    lease_end = fields.Date(string="Lease End", tracking=True)
    rent_amount = fields.Float(string="Rent Amount", tracking=True)
    water_tank = fields.Char(string="Water Tank", tracking=True)

    # 🔹 Meters & Charges
    electricity_meter = fields.Char(string="Electricity Meter", tracking=True)
    water_meter = fields.Char(string="Water Meter", tracking=True)
    internet_bill = fields.Char(string="Internet Bill", tracking=True)
    maintenance_charges = fields.Float(string="Maintenance Charges", tracking=True)
    unit_property_tax = fields.Char(string="Unit Property Tax", tracking=True)
    water_tax = fields.Char(string="Water Tax", tracking=True)

    # 🔹 Relations
    floor_id = fields.Many2one('estate.floor', string="Floor", tracking=True)
    building_id = fields.Many2one(
        "estate.building", store=True, string="Building", tracking=True
    )
    property_id = fields.Many2one(
        "estate.property", store=True, string="Property", tracking=True
    )

    # 🔹 Rooms
    room_ids = fields.One2many('estate.room', 'unit_id', string="Rooms", tracking=True)
    number_of_rooms = fields.Integer(
        string="Number of Rooms",
        compute="_compute_number_of_rooms",
        store=True,
        tracking=True
    )

    # 🔹 Employee count
    employee_count = fields.Integer(
        string="Employee Count",
        compute="_compute_employee_count",
        store=True,tracking=True
    )

    # 🔹 Payments
    payment_ids = fields.One2many('estate.unit.payment', 'unit_id', string="Payments",tracking=True)

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
        'estate_unit_ir_attachment_rel',
        'unit_id',
        'attachment_id',
        string="Unit Documents",tracking=True
    )

    legal_document_count = fields.Integer(
        compute="_compute_legal_document_count",tracking=True
    )
    usage_id = fields.Many2one(
        'estate.property.usage',
        string="Usage",
        ondelete='restrict',
        tracking=True
    )
    internet_service = fields.Char(
        string="Internet Service",
        tracking=True
    )

    # 🔼 UPPER
    hup_property_id = fields.Many2one('estate.property', required=True,string="Property",tracking=True)
    hup_building_id = fields.Many2one('estate.building', required=True,string="Buildings",tracking=True)
    hup_floor_id = fields.Many2one('estate.floor', required=True,string="Floors",tracking=True)

    # 🔽 DOWNER
    hdown_room_ids = fields.Many2many('estate.room',string="Rooms",tracking=True)
    hdown_table_ids = fields.Many2many('estate.room.table',string="Tables",tracking=True)

    # 🔢 COUNTS
    hcount_room = fields.Integer(compute='_compute_hcounts',string="Rooms",tracking=True)
    hcount_table = fields.Integer(compute='_compute_hcounts',string="Tables",tracking=True)

    payment_count = fields.Integer(
        string="Payments",
        compute="_compute_payment_count",
        store=True,tracking=True
    )


    hup_location_id = fields.Many2one(
        'estate.location',
        required=True,
        string="Location",tracking=True
    )
    hcount_location = fields.Integer(
        compute="_compute_location_count",
        string="Location",tracking=True
    )
    unit_number = fields.Char(string="Unit Number", tracking=True)

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


    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)

    @api.depends('hdown_room_ids', 'hdown_table_ids')
    def _compute_hcounts(self):
        for r in self:
            r.hcount_room = len(r.hdown_room_ids)
            r.hcount_table = len(r.hdown_table_ids)

    def haction_open_rooms(self):
        return self._open_hdown(
            'Rooms',
            'estate.room',
            self.hdown_room_ids,
            {
                'default_hup_unit_id': self.id,
                'default_hup_floor_id': self.hup_floor_id.id,
                'default_hup_building_id': self.hup_building_id.id,
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
                'default_hup_unit_id': self.id,
                'default_hup_floor_id': self.hup_floor_id.id,
                'default_hup_building_id': self.hup_building_id.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    @api.depends('legal_document_ids')
    def _compute_legal_document_count(self):
        for rec in self:
            rec.legal_document_count = len(rec.legal_document_ids)

    def action_open_legal_documents(self):
        self.ensure_one()
        return {
            'name': 'Unit Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.legal_document_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }

    def action_open_payments(self):
        self.ensure_one()
        return {
            'name': 'Payments',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.unit.payment',
            'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'context': {
                'default_unit_id': self.id,
                'default_building_id': self.hup_building_id.id,
                'default_property_id': self.hup_property_id.id,
            }
        }
    # -------------------------------
    # COMPUTE METHODS
    # -------------------------------
    @api.depends('room_ids')
    def _compute_number_of_rooms(self):
        for unit in self:
            unit.number_of_rooms = len(unit.room_ids)

    @api.depends('room_ids.employee_count')
    def _compute_employee_count(self):
        for unit in self:
            unit.employee_count = sum(room.employee_count for room in unit.room_ids)


    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = super(EstateUnit, self).create(vals_list)
    #
    #     for record, vals in zip(records, vals_list):
    #         if vals.get('unit_code'):
    #             record.unit_code_locked = True
    #
    #         log_items = []
    #         for key, value in vals.items():
    #             field = self._fields.get(key)
    #
    #             # 🛡️ Skip if field doesn't exist, is relational (X2many), or is HTML/Binary
    #             if not field or field.type in ['one2many', 'many2many', 'html', 'binary']:
    #                 continue
    #
    #             # 🚫 Skip empty/falsey values
    #             if not value and value != 0 and value is not False:
    #                 continue
    #
    #             field_label = field.string
    #             display_value = value
    #
    #             # Handle Many2one display names
    #             if field.type == 'many2one' and value:
    #                 display_value = self.env[field.comodel_name].browse(value).display_name
    #
    #             log_items.append(f"<b>{field_label}</b>: {display_value}")
    #
    #         if log_items:
    #             # 💡 Use Markup() here to ensure HTML tags render correctly in Odoo 16+
    #             message_body = Markup(_("Unit created with values:<br/>%s") % "<br/>".join(log_items))
    #
    #             record.message_post(
    #                 body=message_body
    #             )
    #     return records
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = super().create(vals_list)
    #     for r in records:
    #         r._add_to_parent(r.hup_floor_id, 'hdown_unit_ids')
    #         r._add_to_parent(r.hup_building_id, 'hdown_unit_ids')
    #         r._add_to_parent(r.hup_property_id, 'hdown_unit_ids')
    #     return records

    @api.model_create_multi
    def create(self, vals_list):

        # 🔕 Disable default mail.thread chatter
        self = self.with_context(tracking_disable=True)

        records = super(EstateUnit, self).create(vals_list)

        for record, vals in zip(records, vals_list):

            # 🔒 LOCK UNIT CODE (SILENT)
            if vals.get('unit_code'):
                record.with_context(tracking_disable=True).write({
                    'unit_code_locked': True
                })
            if record.hup_location_id:
                record._add_to_parent(
                    record.hup_location_id,
                    'hdown_unit_ids'
                )

            # 🌳 ADD TO HIERARCHY (SAME FLOW AS FLOOR)
            if record.hup_floor_id:
                record._add_to_parent(record.hup_floor_id, 'hdown_unit_ids')

            if record.hup_building_id:
                record._add_to_parent(record.hup_building_id, 'hdown_unit_ids')

            if record.hup_property_id:
                record._add_to_parent(record.hup_property_id, 'hdown_unit_ids')

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

                log_items.append(f"<b>{field.string}</b>: {display_value}")

            if log_items:
                record.message_post(
                    body=Markup(
                        _("Unit created with values:<br/>%s")
                        % "<br/>".join(log_items)
                    )
                )

        return records

    # -------------------------------
    # WRITE
    # -------------------------------
    # def write(self, vals):
    #
    #     # ✅ BLOCK CODE CHANGE AFTER SAVE
    #     if 'unit_code' in vals:
    #         for rec in self:
    #             if rec.unit_code_locked:
    #                 raise ValidationError(_("Unit Code cannot be changed once saved."))
    #
    #     # EXISTING CHANGE TRACKING (UNCHANGED)
    #     changes_dict = {}
    #     for record in self:
    #         changes = []
    #         for field, new_value in vals.items():
    #             if isinstance(new_value, (list, tuple)):
    #                 continue
    #
    #             old_value = record[field]
    #             if old_value != new_value:
    #                 old_display = (
    #                     old_value.display_name
    #                     if hasattr(old_value, 'display_name')
    #                     else old_value
    #                 )
    #                 field_label = self._fields[field].string if field in self._fields else field
    #                 changes.append(f"<b>{field_label}</b>: {old_display} → {new_value}")
    #
    #         if changes:
    #             changes_dict[record.id] = "<br/>".join(changes)
    #
    #     res = super(EstateUnit, self).write(vals)
    #
    #     # POST CHATTER + LOCK CODE
    #     for record in self:
    #         if record.id in changes_dict:
    #             record.message_post(
    #                 body=_("Updated fields:<br/>%s") % changes_dict[record.id]
    #             )
    #
    #     if 'unit_code' in vals:
    #         self.filtered(
    #             lambda r: r.unit_code and not r.unit_code_locked
    #         ).write({'unit_code_locked': True})
    #
    #     return res
    def write(self, vals):

        # ❌ BLOCK UNIT CODE CHANGE
        if 'unit_code' in vals:
            for rec in self:
                if rec.unit_code_locked:
                    raise ValidationError(
                        _("Unit Code cannot be changed once saved.")
                    )

        # 🧾 PREPARE CHATTER (SAFE COMPARISON)
        changes_dict = {}
        for record in self:
            changes = []

            for field_name, new_value in vals.items():

                if field_name in ('unit_code_locked',):
                    continue

                field = record._fields.get(field_name)
                if not field:
                    continue
                if field.type in ('one2many', 'many2many', 'html', 'binary'):
                    continue

                old_value = record[field_name]

                # ✅ FIX: normalize before comparison
                if field.type == 'many2one':
                    old_compare = old_value.id if old_value else False
                    new_compare = new_value
                else:
                    old_compare = old_value
                    new_compare = new_value

                if old_compare == new_compare:
                    continue

                old_display = (
                    old_value.display_name
                    if hasattr(old_value, 'display_name')
                    else old_value
                )

                new_display = new_value
                if field.type == 'many2one' and isinstance(new_value, int):
                    new_display = record.env[field.comodel_name].browse(new_value).display_name

                changes.append(
                    f"<b>{field.string}</b>: {old_display} → {new_display}"
                )

            if changes:
                changes_dict[record.id] = "<br/>".join(changes)

        # 🔕 Disable default tracking
        res = super(EstateUnit, self.with_context(tracking_disable=True)).write(vals)

        # 🔒 LOCK UNIT CODE (SILENT)
        if 'unit_code' in vals:
            self.filtered(
                lambda r: r.unit_code and not r.unit_code_locked
            ).with_context(tracking_disable=True).write({
                'unit_code_locked': True
            })

        # 🧾 POST CHATTER
        for record in self:
            if record.id in changes_dict:
                record.message_post(
                    body=Markup(
                        _("Updated fields:<br/>%s") % changes_dict[record.id]
                    )
                )

        return res


# ==========================================================
# 🔹 Payment Types
# ==========================================================
class EstatePaymentType(models.Model):
    _name = "estate.payment.type"
    _description = "Payment Types"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(string="Payment Type", required=True, index=True,tracking=True)
    active = fields.Boolean(default=True,tracking=True)














# from odoo import models, fields, api, _
#
# class EstateUnit(models.Model):
#     _name = 'estate.unit'
#     _inherit = ['mail.thread']
#     _description = 'Unit'
#
#     # 🔹 Basic Info
#     name = fields.Char(string="Unit Name", required=True, tracking=True)
#     unit_type = fields.Selection([
#         ('residential', 'Residential'),
#         ('commercial', 'Commercial')
#     ], string="Unit Type", tracking=True)
#     area_sqft = fields.Float(string="Area (sq.ft)", tracking=True)
#     occupancy_status = fields.Selection([
#         ('vacant', 'Vacant'),
#         ('occupied', 'Occupied')
#     ], string="Occupancy Status", tracking=True)
#     tenant = fields.Char(string="Tenant", tracking=True)
#     lease_start = fields.Date(string="Lease Start", tracking=True)
#     lease_end = fields.Date(string="Lease End", tracking=True)
#     rent_amount = fields.Float(string="Rent Amount", tracking=True)
#
#     # 🔹 Meters & Charges
#     electricity_meter = fields.Char(string="Electricity Meter", tracking=True)
#     water_meter = fields.Char(string="Water Meter", tracking=True)
#     internet_bill = fields.Char(string="Internet Bill", tracking=True)
#     maintenance_charges = fields.Float(string="Maintenance Charges", tracking=True)
#     unit_property_tax = fields.Char(string="Unit Property Tax", tracking=True)
#     water_tax = fields.Char(string="Water Tax", tracking=True)
#
#     # 🔹 Relations
#     floor_id = fields.Many2one('estate.floor', string="Floor",required=True, tracking=True)
#     building_id = fields.Many2one(related="floor_id.building_id", store=True, string="Building",required=True, tracking=True)
#     property_id = fields.Many2one(related="building_id.property_id", store=True, string="Property",required=True, tracking=True)
#
#     # 🔹 Rooms
#     room_ids = fields.One2many('estate.room', 'unit_id', string="Rooms", tracking=True)
#     number_of_rooms = fields.Integer(string="Number of Rooms", compute="_compute_number_of_rooms", store=True, tracking=True)
#
#     # 🔹 Employee count across rooms
#     employee_count = fields.Integer(string="Employee Count", compute="_compute_employee_count", store=True)
#
#     # 🔹 Payments
#     payment_ids = fields.One2many('estate.unit.payment', 'unit_id', string="Payments")
#
#     # -------------------------------
#     # COMPUTE METHODS
#     # -------------------------------
#     @api.depends('room_ids')
#     def _compute_number_of_rooms(self):
#         for unit in self:
#             unit.number_of_rooms = len(unit.room_ids)
#
#     @api.depends('room_ids.employee_count')
#     def _compute_employee_count(self):
#         for unit in self:
#             unit.employee_count = sum(room.employee_count for room in unit.room_ids)
#
#     # -------------------------------
#     # OVERRIDES: CREATE & WRITE
#     # -------------------------------
#     @api.model
#     def create(self, vals):
#         record = super().create(vals)
#         message = _("Unit created with values:<br/>%s") % "<br/>".join(
#             [f"<b>{field}</b>: {vals[field]}" for field in vals]
#         )
#         record.message_post(body=message)
#         return record
#
#     def write(self, vals):
#         for record in self:
#             changes = []
#             for field in vals:
#                 old_value = record[field]
#                 new_value = vals[field]
#                 changes.append(f"<b>{field}</b>: {old_value} → {new_value}")
#             if changes:
#                 message = _("Updated fields:<br/>%s") % "<br/>".join(changes)
#                 record.message_post(body=message)
#         return super().write(vals)
#
#
# # ==========================================================
# # 🔹 Child Model: Payment
# # ==========================================================
# class EstateUnitPayment(models.Model):
#     _name = 'estate.unit.payment'
#     _description = 'Unit Payment'
#
#     unit_id = fields.Many2one('estate.unit', string="Unit", ondelete='cascade', required=True)
#     payment_for_id = fields.Many2one('estate.payment.type', string="Payment For", required=True)
#     payment_for = fields.Char(related="payment_for_id.name", string="Payment For (Text)", store=True, readonly=True)
#     meter_start_reading = fields.Float(string="Meter Start Reading")
#     meter_end_reading = fields.Float(string="Meter End Reading")
#     meter_consumed = fields.Float(string="Consumed Units", compute="_compute_consumed", store=True)
#     amount = fields.Float(string="Amount", required=True)
#     due_date = fields.Date(string="Due Date")
#
#     @api.depends('meter_start_reading', 'meter_end_reading')
#     def _compute_consumed(self):
#         for rec in self:
#             rec.meter_consumed = (rec.meter_end_reading - rec.meter_start_reading) if rec.meter_end_reading and rec.meter_start_reading else 0.0
#
#
# # ==========================================================
# # 🔹 Payment Types
# # ==========================================================
# class EstatePaymentType(models.Model):
#     _name = "estate.payment.type"
#     _description = "Payment Types"
#
#     name = fields.Char(string="Payment Type", required=True, index=True)
#     active = fields.Boolean(default=True)
