from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from markupsafe import Markup


class EstateFloor(models.Model):
    _name = 'estate.floor'
    _inherit = ['mail.thread', 'estate.hierarchy.mixin','delete.notification.mixin']
    _description = 'Floor'
    _rec_name = 'name'

    # === Basic Info ===
    name = fields.Char(string="Floor Name", required=True, tracking=True)
    building_id = fields.Many2one(
        'estate.building',
        string="Building",
        ondelete='cascade',
        tracking=True
    )
    # ✅ ADDED (CODE LOGIC)
    floor_code = fields.Char(string="Floor Code", tracking=True,required=True)
    floor_code_locked = fields.Boolean(default=False)
    property_id = fields.Many2one(
        "estate.property",
        store=True,
        string="Property",
        tracking=True,
    )
    access = fields.Char(string="Access", tracking=True)
    access_id = fields.Many2one(
        'estate.floor.access',
        string="Access",
        tracking=True,
        ondelete='restrict'
    )

    corridor_lighting = fields.Char(string="Corridor Lighting", tracking=True)
    water_tank = fields.Char(string="Water Tank", tracking=True)

    # === Relations ===
    unit_ids = fields.One2many('estate.unit', 'floor_id', string="Units", tracking=True)

    # === Computed Fields ===
    number_of_units = fields.Integer(compute="_compute_counts", string="Number of Units", tracking=True)
    number_of_rooms = fields.Integer(compute="_compute_counts", string="Number of Rooms", tracking=True)
    employee_count = fields.Integer(compute="_compute_employee_count", store=True, string="Employees",tracking=True)

    hup_property_id = fields.Many2one('estate.property', required=True, string="Property",tracking=True)
    hup_building_id = fields.Many2one('estate.building', required=True,string="Building",tracking=True)

    # 🔽 DOWNER
    hdown_unit_ids = fields.Many2many('estate.unit',string="Units",tracking=True)
    hdown_room_ids = fields.Many2many('estate.room',string="Rooms",tracking=True)
    hdown_table_ids = fields.Many2many('estate.room.table',string="Tables",tracking=True)

    # 🔢 COUNTS
    hcount_unit = fields.Integer(compute='_compute_hcounts',string="Units",tracking=True)
    hcount_room = fields.Integer(compute='_compute_hcounts',string="Rooms",tracking=True)
    hcount_table = fields.Integer(compute='_compute_hcounts',string="Tables",tracking=True)


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
    @api.depends('hdown_unit_ids', 'hdown_room_ids', 'hdown_table_ids')
    def _compute_hcounts(self):
        for r in self:
            r.hcount_unit = len(r.hdown_unit_ids)
            r.hcount_room = len(r.hdown_room_ids)
            r.hcount_table = len(r.hdown_table_ids)

    def haction_open_units(self):
        return self._open_hdown(
            'Units',
            'estate.unit',
            self.hdown_unit_ids,
            {
                'default_hup_floor_id': self.id,
                'default_hup_building_id': self.hup_building_id.id,
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
                'default_hup_floor_id': self.id,
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
                'default_hup_floor_id': self.id,
                'default_hup_building_id': self.hup_building_id.id,
                'default_hup_property_id': self.hup_property_id.id,
                'default_hup_location_id': self.hup_location_id.id,
            }
        )

    # === Compute Methods ===
    @api.depends('unit_ids', 'unit_ids.room_ids')
    def _compute_counts(self):
        """Count units and rooms under this floor."""
        for floor in self:
            floor.number_of_units = len(floor.unit_ids)
            floor.number_of_rooms = sum(len(unit.room_ids) for unit in floor.unit_ids)

    @api.depends('unit_ids.employee_count')
    def _compute_employee_count(self):
        """Aggregate employees from units."""
        for floor in self:
            floor.employee_count = sum(unit.employee_count for unit in floor.unit_ids)



    # -------------------------------
    # WRITE
    # -------------------------------
    def write(self, vals):

        # ❌ BLOCK FLOOR CODE CHANGE
        if 'floor_code' in vals:
            for rec in self:
                if rec.floor_code_locked:
                    raise ValidationError(
                        _("Floor Code cannot be changed once saved.")
                    )

        # 🧾 PREPARE CHATTER
        changes_dict = {}
        for record in self:
            changes = []
            for field_name, new_value in vals.items():

                if field_name in ('floor_code_locked',):
                    continue

                field = record._fields.get(field_name)
                if not field:
                    continue
                if field.type in ('one2many', 'many2many', 'html', 'binary'):
                    continue

                old_value = record[field_name]
                if old_value == new_value:
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

        # ✅ disable default tracking safely
        res = super(EstateFloor, self.with_context(tracking_disable=True)).write(vals)

        # 🔒 LOCK FLOOR CODE (SILENT)
        if 'floor_code' in vals:
            self.filtered(
                lambda r: r.floor_code and not r.floor_code_locked
            ).with_context(tracking_disable=True).write({
                'floor_code_locked': True
            })

        # 🧾 POST CHATTER
        for record in self:
            if record.id in changes_dict:
                record.message_post(
                    body=_("Updated fields:<br/>%s") % changes_dict[record.id]
                )

        return res


    @api.model_create_multi
    def create(self, vals_list):

        # ✅ disable tracking at recordset level
        self = self.with_context(tracking_disable=True)

        records = super(EstateFloor, self).create(vals_list)

        for record, vals in zip(records, vals_list):

            # 🔒 LOCK FLOOR CODE (SILENT)
            if vals.get('floor_code'):
                record.with_context(tracking_disable=True).write({
                    'floor_code_locked': True
                })
            if record.hup_location_id:
                record._add_to_parent(
                    record.hup_location_id,
                    'hdown_floor_ids'
                )

            # 🌳 ADD TO HIERARCHY
            if record.hup_building_id:
                record._add_to_parent(record.hup_building_id, 'hdown_floor_ids')

            if record.hup_property_id:
                record._add_to_parent(record.hup_property_id, 'hdown_floor_ids')

            # 🧾 CUSTOM CHATTER
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
                        _("Floor created with values:<br/>%s")
                        % "<br/>".join(log_items)
                    )
                )

        return records


class EstateFloorAccess(models.Model):
    _name = 'estate.floor.access'
    _description = 'Floor Access Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(string="Access Type", required=True)
    code = fields.Char(string="Code",tracking=True)
    active = fields.Boolean(default=True,tracking=True)
