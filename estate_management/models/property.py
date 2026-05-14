from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
# import pgeocode
#
# nomi = pgeocode.Nominatim('in')  # India

class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Property Type'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']


    name = fields.Char(required=True,tracking=True)
    active = fields.Boolean(default=True,tracking=True)


# =================================================
# PROPERTY USAGE MASTER
# =================================================
class EstatePropertyUsage(models.Model):
    _name = 'estate.property.usage'
    _description = 'Property Usage'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    active = fields.Boolean(default=True,tracking=True)


# =================================================
# PROPERTY OWNER MASTER
# =================================================
class EstatePropertyOwner(models.Model):
    _name = 'estate.property.owner'
    _description = 'Property Owner'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True)
    mobile = fields.Char(tracking=True)
    email = fields.Char(tracking=True)
    address = fields.Text(tracking=True)
    active = fields.Boolean(default=True)

    @api.constrains('mobile', 'email')
    def _check_contact_fields(self):

        for rec in self:

            # Mobile validation (10 digits)
            if rec.mobile:
                if not re.fullmatch(r"\d{10}", rec.mobile):
                    raise ValidationError(
                        _("Mobile number must contain exactly 10 digits.")
                    )

            # Email validation
            if rec.email:
                if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", rec.email):
                    raise ValidationError(
                        _("Please enter a valid email address.")
                    )

class EstateProperty(models.Model):
    _name = 'estate.property'
    _inherit = ['mail.thread','mail.activity.mixin', 'estate.hierarchy.mixin',  'estate.security.mixin','delete.notification.mixin']
    _description = 'Property'
    _rec_name = 'name'
    _order = "id desc"

    # === Basic Info ===
    name = fields.Char(string="Property Name", required=True, tracking=True)
    location = fields.Char(string="Property Address", tracking=True)
    property_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial')
    ], string="Property Type", tracking=True)
    usage = fields.Char(string="Usage", tracking=True)
    owner = fields.Char(string="Owner", tracking=True)
    legal_document_ids = fields.Many2many(
        'ir.attachment',
        'estate_property_ir_attachment_rel',
        'property_id',
        'attachment_id',
        string="Documents",tracking=True
    )

    property_type_id= fields.Many2one(
        'estate.property.type',
        string="Property Type",
        ondelete='restrict',
        tracking=True
    )

    usage_id= fields.Many2one(
        'estate.property.usage',
        string="Usage",
        ondelete='restrict',
        tracking=True
    )

    owner_id = fields.Many2one(
        'estate.property.owner',
        string="Owner",
        ondelete='restrict',
        tracking=True
    )

    # --- Attachments ---
    legal_document_ids_id = fields.Many2many(
        'ir.attachment',
        'estate_property_ir_attachment_rel',
        'property_id',
        'attachment_id',
        string="Documents",tracking=True
    )

    legal_document_count = fields.Integer(
        compute='_compute_legal_document_count',tracking=True
    )

    # === NEW FIELDS (PROPERTY) ===
    property_number = fields.Char(string="Property Number", tracking=True)

    address = fields.Text(string="Address", tracking=True)
    city = fields.Char(string="City / Town / Village", tracking=True)
    state = fields.Char(string="State", tracking=True)
    pincode = fields.Char(string="Pincode", tracking=True)

    responsible_employee_id = fields.Many2one(
        'res.partner',
        string="Responsible Employee",
        tracking=True
    )
    # 🔽 DOWNER
    hdown_building_ids = fields.Many2many('estate.building',string="Buildings",tracking=True)
    hdown_floor_ids = fields.Many2many('estate.floor',string="Floor",tracking=True)
    hdown_unit_ids = fields.Many2many('estate.unit',string="Units",tracking=True)
    hdown_room_ids = fields.Many2many('estate.room',string="Rooms",tracking=True)
    hdown_table_ids = fields.Many2many('estate.room.table',string="Tables",tracking=True)
    # 🔽 DOWNER (ADD THIS)
    hdown_farm_ids = fields.Many2many('estate.farm',string="Farms",tracking=True)

    # 🔢 COUNT (ADD THIS)

    # 🔢 COUNTS
    hcount_building = fields.Integer(compute='_compute_hcounts',string="Buildings",tracking=True)
    hcount_floor = fields.Integer(compute='_compute_hcounts',string="Floors",tracking=True)
    hcount_unit = fields.Integer(compute='_compute_hcounts',string="Units",tracking=True)
    hcount_room = fields.Integer(compute='_compute_hcounts',string="Rooms",tracking=True)
    hcount_table = fields.Integer(compute='_compute_hcounts',string="Tables",tracking=True)
    hcount_farm = fields.Integer(compute='_compute_hcounts',string="Farms",tracking=True)
    hup_location_id = fields.Many2one(
        'estate.location',
        required=True,
        string="Location",tracking=True
    )
    hcount_location = fields.Integer(
        compute='_compute_location_count',
        string="Location",tracking=True
    )

    location_id = fields.Many2one(
        'custom.location',tracking=True
    )
    map_url = fields.Html(
        related='location_id.map_url',
        string="Google Map",tracking=True
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

            # Show only this property's locations
            'domain': [('property_id', '=', self.id)],

            # Auto default when creating new
            'context': {
                'default_property_id': self.id,
            }
        }

    @api.depends('hup_location_id')
    def _compute_location_count(self):
        for rec in self:
            rec.hcount_location = 1 if rec.hup_location_id else 0

    def haction_open_location(self):
        return self._open_hup(
            'Location',
            'estate.location',
            self.hup_location_id
        )

    def action_open_location(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Location',
            'res_model': 'estate.location',
            'view_mode': 'form',
            'res_id': self.hup_location_id.id,
        }


    @api.depends(
        'hdown_building_ids',
        'hdown_floor_ids',
        'hdown_unit_ids',
        'hdown_room_ids',
        'hdown_table_ids',
        'hdown_farm_ids',
    )
    def _compute_hcounts(self):
        for r in self:
            r.hcount_building = len(r.hdown_building_ids)
            r.hcount_floor = len(r.hdown_floor_ids)
            r.hcount_unit = len(r.hdown_unit_ids)
            r.hcount_room = len(r.hdown_room_ids)
            r.hcount_table = len(r.hdown_table_ids)
            r.hcount_farm = len(r.hdown_farm_ids)

            # 🔘 SMART BUTTONS
    # def haction_open_buildings(self):
    #     return self._open_hdown('Buildings', 'estate.building', self.hdown_building_ids)
    def haction_open_buildings(self):
        return self._open_hdown(
            'Buildings',
            'estate.building',
            self.hdown_building_ids,
            {
                'default_hup_property_id': self.id,  # 🔥 THIS IS THE KEY
                'default_hup_location_id': self.hup_location_id.id,

            }
        )

    def haction_open_floors(self):
        return self._open_hdown(
            'Floors',
            'estate.floor',
            self.hdown_floor_ids,
            {
                'default_hup_property_id': self.id,
                'default_hup_location_id': self.hup_location_id.id,

            }
        )

    def haction_open_units(self):
        return self._open_hdown(
            'Units',
            'estate.unit',
            self.hdown_unit_ids,
            {
                'default_hup_property_id': self.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    def haction_open_rooms(self):
        return self._open_hdown(
            'Rooms',
            'estate.room',
            self.hdown_room_ids,
            {
                'default_hup_property_id': self.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    def haction_open_tables(self):
        return self._open_hdown(
            'Tables',
            'estate.room.table',
            self.hdown_table_ids,
            {
                'default_hup_property_id': self.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    def haction_open_farms(self):
        self.ensure_one()
        return {
            'name': 'Farms',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.farm',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('estate_management.view_farm_list').id, 'list'),
                (self.env.ref('estate_management.view_farm_form').id, 'form'),  # ✅ FIX
            ],
            'domain': [('id', 'in', self.hdown_farm_ids.ids)],
            'context': {
                'default_hup_property_id': self.id,
                'default_hup_location_id': self.hup_location_id.id,

            }
        }

    @api.depends('legal_document_ids')
    def _compute_legal_document_count(self):
        for rec in self:
            rec.legal_document_count = len(rec.legal_document_ids)

    def action_open_legal_documents(self):
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.legal_document_ids.ids)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }


    # legal_documents = fields.Binary(string="Legal Documents", tracking=True)

    # === Taxes & Meters ===
    # property_tax = fields.Integer(string="Property Tax", tracking=True)
    # land_tax = fields.Integer(string="Land Tax", tracking=True)
    # municipal_tax = fields.Integer(string="Municipal Tax", tracking=True)
    property_tax = fields.Char(string="Property Tax", tracking=True)
    land_tax = fields.Char(string="Land Tax", tracking=True)
    municipal_tax = fields.Char(string="Municipal Tax", tracking=True)
    electricity_meter = fields.Char(string="Electricity Meter", tracking=True)
    water_meter = fields.Char(string="Water Meter", tracking=True)
    gas_meter = fields.Char(string="Gas Meter", tracking=True)
    property_code = fields.Char(string="Property Code", tracking=True,required=True)
    property_code_locked = fields.Boolean(default=False,tracking=True)
    # === Relations ===
    building_ids = fields.One2many('estate.building', 'property_id', string="Buildings", tracking=True)
    farm_ids = fields.One2many('estate.farm', 'property_id', string="Farms",tracking=True)

    # === Computed Fields ===
    number_of_buildings = fields.Integer(compute="_compute_counts", string="Number of Buildings", tracking=True)
    number_of_floors = fields.Integer(compute="_compute_counts", string="Number of Floors", tracking=True)
    number_of_units = fields.Integer(compute="_compute_counts", string="Number of Units", tracking=True)
    number_of_rooms = fields.Integer(compute="_compute_counts", string="Number of Rooms", tracking=True)
    employee_count = fields.Integer(compute="_compute_employee_count", store=True, string="Employees",tracking=True)


    # 🔼 UPPER

    # === Compute Methods ===
    @api.depends(
        'hdown_building_ids',
        'hdown_floor_ids',
        'hdown_unit_ids',
        'hdown_room_ids'
    )
    def _compute_counts(self):
        for record in self:
            record.number_of_buildings = len(record.hdown_building_ids)
            record.number_of_floors = len(record.hdown_floor_ids)
            record.number_of_units = len(record.hdown_unit_ids)
            record.number_of_rooms = len(record.hdown_room_ids)

    @api.depends('building_ids.employee_count')
    def _compute_employee_count(self):
        for record in self:
            record.employee_count = sum(b.employee_count for b in record.building_ids)

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for record, vals in zip(records, vals_list):

            if vals.get('property_code'):
                record.property_code_locked = True

            if record.hup_location_id:
                record._add_to_parent(
                    record.hup_location_id,
                    'hdown_property_ids'
                )

        return records

    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = super().create(vals_list)
    #
    #     for record, vals in zip(records, vals_list):
    #         if vals.get('property_code'):
    #             record.property_code_locked = True
    #         if record.hup_location_id:
    #             record._add_to_parent(
    #                 record.hup_location_id,
    #                 'hdown_property_ids'
    #             )
    #         if not vals.get('location_id'):
    #             location = self.env['custom.location'].create({})
    #             vals['location_id'] = location.id
    #
    #     return records

    # -------------------------------
    # WRITE
    # -------------------------------
    def write(self, vals):
        if 'property_code' in vals:
            for rec in self:
                if rec.property_code_locked:
                    raise ValidationError(_("Property Code cannot be changed once saved."))

        res = super().write(vals)

        if 'property_code' in vals:
            self.filtered(
                lambda r: r.property_code and not r.property_code_locked
            ).write({'property_code_locked': True})

        return res




    # === Actions ===
    def action_open_buildings(self):
        """Open all buildings linked to this property in tree+form view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Buildings'),
            'res_model': 'estate.building',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('estate_management.view_building_tree').id, 'tree'),
                (self.env.ref('estate_management.view_building_form').id, 'form')
            ],
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id,
                        'default_hup_location_id': self.hup_location_id.id,},
        }




class ResConfigSettings(models.TransientModel):
        _inherit = 'res.config.settings'
        _order = "id desc"

        enable_ocn = fields.Boolean(
            string="Enable OCN",
            config_parameter='estate_management.enable_ocn',tracking=True
        )
        disable_redirect_firebase_dynamic_link = fields.Boolean(
            string="Disable Firebase Dynamic Link Redirect",
            config_parameter='estate_management.disable_redirect_firebase_dynamic_link',tracking=True
        )




