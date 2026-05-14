from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from markupsafe import Markup


class EstateRoom(models.Model):
    _name = 'estate.room'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.hierarchy.mixin','estate.security.mixin','delete.notification.mixin']
    _description = 'Room'
    _rec_name = 'name'
    _order = "id desc"

    # 🔹 Basic Info
    name = fields.Char(string="Room Name", required=True, tracking=True)
    unit_id = fields.Many2one('estate.unit', string="Unit",  tracking=True)
    floor_id = fields.Many2one('estate.floor', string="Floor", tracking=True)
    building_id = fields.Many2one(
        "estate.building", store=True, string="Building", tracking=True
    )
    property_id = fields.Many2one(
        "estate.property", store=True, string="Property", tracking=True
    )

    size_sqft = fields.Float(string="Size (sq.ft)", tracking=True)

    room_type = fields.Selection([
        ('bedroom', 'Bedroom'),
        ('living', 'Living Room'),
        ('kitchen', 'Kitchen'),
        ('bathroom', 'Bathroom'),
        ('other', 'Other')
    ], string="Room Type", tracking=True)

    room_type_id = fields.Many2one(
        'estate.room.type',
        string="Room Type",
        tracking=True,
        ondelete='restrict'
    )

    furniture = fields.Text(string="Furniture", tracking=True)
    appliances = fields.Text(string="Appliances", tracking=True)

    # 🔹 Employees
    employee_ids = fields.One2many('estate.room.employee', 'room_id', string="Employees",tracking=True)
    employee_count = fields.Integer(
        string="Employee Count", compute="_compute_employee_count", store=True,tracking=True
    )

    # 🔒 Room Code
    code = fields.Char(string="Room Code", tracking=True,required=True)
    code_locked = fields.Boolean(default=False,tracking=True)

    # 🔼 UPPER
    hup_property_id = fields.Many2one('estate.property', required=True,string="Property",tracking=True)
    hup_building_id = fields.Many2one('estate.building', required=True,string="Buildings",tracking=True)
    hup_floor_id = fields.Many2one('estate.floor', required=True,string="Floors",tracking=True)
    hup_unit_id = fields.Many2one('estate.unit', required=True,string="Units",tracking=True)

    # 🔽 DOWNER
    hdown_table_ids = fields.Many2many('estate.room.table',string="Tables",tracking=True)

    # 🔢 COUNT
    hcount_table = fields.Integer(compute='_compute_hcounts',string="Tables",tracking=True)
    table_id = fields.Many2one(
        'estate.room.table',
        string="Table",tracking=True
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

    def haction_open_location(self):
        self.ensure_one()
        return {
            'name': 'Location',
            'type': 'ir.actions.act_window',
            'res_model': 'estate.location',
            'view_mode': 'form',
            'res_id': self.hup_location_id.id,
        }

    @api.depends('hup_location_id')
    def _compute_location_count(self):
        for rec in self:
            rec.hcount_location = 1 if rec.hup_location_id else 0
    @api.depends('hdown_table_ids')
    def _compute_hcounts(self):
        for r in self:
            r.hcount_table = len(r.hdown_table_ids)

    def haction_open_tables(self):
        return self._open_hdown(
            'Tables',
            'estate.room.table',
            self.hdown_table_ids,
            {
                'default_hup_room_id': self.id,
                'default_hup_unit_id': self.hup_unit_id.id,
                'default_hup_floor_id': self.hup_floor_id.id,
                'default_hup_building_id': self.hup_building_id.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    # -------------------------------
    # COMPUTES
    # -------------------------------
    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for room in self:
            room.employee_count = len(room.employee_ids)

    # -------------------------------
    # ONCHANGE
    # -------------------------------
    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        if self.unit_id:
            self.floor_id = self.unit_id.floor_id




    # -------------------------------
    # WRITE
    # -------------------------------
    def write(self, vals):

        # ❌ BLOCK ROOM CODE CHANGE
        if 'code' in vals:
            for rec in self:
                if rec.code_locked:
                    raise ValidationError(
                        _("Room Code cannot be changed once saved.")
                    )

        # 🔁 AUTO-SET FLOOR FROM UNIT
        if vals.get('unit_id'):
            unit = self.env['estate.unit'].browse(vals['unit_id'])
            vals['floor_id'] = unit.floor_id.id if unit.floor_id else False

        # 🧾 PREPARE CHATTER (SAFE COMPARISON)
        changes_dict = {}
        for record in self:
            changes = []

            for field_name, new_value in vals.items():

                if field_name in ('code_locked',):
                    continue

                field = record._fields.get(field_name)
                if not field:
                    continue
                if field.type in ('one2many', 'many2many', 'html', 'binary'):
                    continue

                old_value = record[field_name]

                # ✅ NORMALIZE BEFORE COMPARISON
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
        res = super(EstateRoom, self.with_context(tracking_disable=True)).write(vals)

        # 🔒 LOCK ROOM CODE (SILENT)
        if 'code' in vals:
            self.filtered(
                lambda r: r.code and not r.code_locked
            ).with_context(tracking_disable=True).write({
                'code_locked': True
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

    @api.model_create_multi
    def create(self, vals_list):

        # 🔕 Disable default mail.thread chatter
        self = self.with_context(tracking_disable=True)

        records = super(EstateRoom, self).create(vals_list)

        for record, vals in zip(records, vals_list):

            # 🔒 LOCK ROOM CODE (SILENT)
            if vals.get('code'):
                record.with_context(tracking_disable=True).write({
                    'code_locked': True
                })
            if record.hup_location_id:
                record._add_to_parent(
                    record.hup_location_id,
                    'hdown_room_ids'
                )

            # 🌳 ADD TO HIERARCHY
            if record.hup_unit_id:
                record._add_to_parent(record.hup_unit_id, 'hdown_room_ids')

            if record.hup_floor_id:
                record._add_to_parent(record.hup_floor_id, 'hdown_room_ids')

            if record.hup_building_id:
                record._add_to_parent(record.hup_building_id, 'hdown_room_ids')

            if record.hup_property_id:
                record._add_to_parent(record.hup_property_id, 'hdown_room_ids')

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
                        _("Room created with values:<br/>%s")
                        % "<br/>".join(log_items)
                    )
                )

        return records


class EstateRoomType(models.Model):
    _name = 'estate.room.type'
    _description = 'Room Type Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(string="Room Type", required=True,tracking=True)
    code = fields.Char(string="Code",tracking=True)
    active = fields.Boolean(default=True,tracking=True)

















# from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError
#
# class EstateRoom(models.Model):
#     _name = 'estate.room'
#     _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']  # Enables chatter & activity tracking
#     _description = 'Room'
#
#     # 🔹 Basic Info
#     name = fields.Char(string="Room Name", required=True, tracking=True)
#     unit_id = fields.Many2one('estate.unit', string="Unit",required=True, tracking=True)
#     floor_id = fields.Many2one('estate.floor', string="Floor", tracking=True)
#     building_id = fields.Many2one(related="floor_id.building_id", store=True, string="Building", tracking=True)
#     property_id = fields.Many2one(related="building_id.property_id", store=True, string="Property", tracking=True)
#
#     size_sqft = fields.Float(string="Size (sq.ft)", tracking=True)
#     room_type = fields.Selection([
#         ('bedroom', 'Bedroom'),
#         ('living', 'Living Room'),
#         ('kitchen', 'Kitchen'),
#         ('bathroom', 'Bathroom'),
#         ('other', 'Other')
#     ], string="Room Type", tracking=True)
#
#     room_type_id = fields.Many2one(
#         'estate.room.type',
#         string="Room Type",
#         tracking=True,
#         ondelete='restrict'
#     )
#
#     furniture = fields.Text(string="Furniture", tracking=True)
#     appliances = fields.Text(string="Appliances", tracking=True)
#
#     # 🔹 Employee Assignment
#     employee_ids = fields.One2many('estate.room.employee', 'room_id', string="Employees")
#     employee_count = fields.Integer(string="Employee Count", compute="_compute_employee_count", store=True)
#     code = fields.Char(string="Room Code", tracking=True)
#     code_locked = fields.Boolean(default=False)
#
#
#
#
#     @api.depends('employee_ids')
#     def _compute_employee_count(self):
#         for room in self:
#             room.employee_count = len(room.employee_ids)
#
#     # 🔹 Auto-set floor_id from unit_id in form onchange
#     @api.onchange('unit_id')
#     def _onchange_unit_id(self):
#         if self.unit_id:
#             self.floor_id = self.unit_id.floor_id
#
#     # -------------------------------
#     # CREATE & WRITE OVERRIDES
#     # # -------------------------------
#     @api.model_create_multi
#     def create(self, vals_list):
#         records = super(EstateRoom, self).create(vals_list)
#         for record, vals in zip(records, vals_list):
#             # Log basic fields, skipping complex relational lists
#             log_items = []
#             for key, value in vals.items():
#                 if not isinstance(value, (list, tuple)):
#                     # Use field label (e.g., "Room Name") instead of technical name (e.g., "name")
#                     field_label = self._fields[key].string if key in self._fields else key
#                     log_items.append(f"<b>{field_label}</b>: {value}")
#
#             if log_items:
#                 message = _("Room created with values:<br/>%s") % "<br/>".join(log_items)
#                 record.message_post(body=message)
#         return records
#
#     def write(self, vals):
#         # 1. Validation & Logic: Block change if locked & Auto-update Floor
#         if 'code' in vals:
#             for rec in self:
#                 if rec.code_locked:
#                     raise ValidationError(_("Room Code cannot be changed once confirmed."))
#
#         if vals.get('unit_id'):
#             unit = self.env['estate.unit'].browse(vals['unit_id'])
#             vals['floor_id'] = unit.floor_id.id
#
#         # 2. Preparation: Capture changes for chatter before database update
#         changes_dict = {}
#         for record in self:
#             changes = []
#             for field, new_val in vals.items():
#                 if isinstance(new_val, (list, tuple)):
#                     continue
#
#                 old_val = record[field]
#                 if old_val != new_val:
#                     # Get readable display name for Many2one fields
#                     old_display = old_val.display_name if hasattr(old_val, 'display_name') else old_val
#                     field_label = self._fields[field].string if field in self._fields else field
#                     changes.append(f"<b>{field_label}</b>: {old_display} → {new_val}")
#
#             if changes:
#                 changes_dict[record.id] = "<br/>".join(changes)
#
#         # 3. Execution: Call the original write
#         res = super(EstateRoom, self).write(vals)
#
#         # 4. Finalization: Post chatter messages & Lock the code
#         for record in self:
#             if record.id in changes_dict:
#                 record.message_post(body=_("Updated fields:<br/>%s") % changes_dict[record.id])
#
#             # Lock logic: only lock if code was just updated and isn't already locked
#             if 'code' in vals and record.code and not record.code_locked:
#                 # Use super().write here to avoid re-triggering this method and validation
#                 super(EstateRoom, record).write({'code_locked': True})
#
#         return res
#
#
# class EstateRoomType(models.Model):
#     _name = 'estate.room.type'
#     _description = 'Room Type Master'
#     _rec_name = 'name'
#
#     name = fields.Char(string="Room Type", required=True)
#     code = fields.Char(string="Code")
#     active = fields.Boolean(default=True)
