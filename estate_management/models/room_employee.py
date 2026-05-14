from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from markupsafe import Markup


class EstateRoomEmployee(models.Model):
    _name = 'estate.room.employee'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']
    _description = 'Room Employee Assignment'
    _rec_name = 'employee_id'
    _order = "id desc"
    _sql_constraints = [
        (
            'uniq_employee_room_table',
            'unique(employee_id, room_id, table_id)',
            'This employee is already assigned to this table in this room.'
        )
    ]

    # -------------------------------------------------
    # BASIC FIELDS
    # -------------------------------------------------
    room_id = fields.Many2one(
        'estate.room',
        string="Room",
        related="table_id.hup_room_id",
        required=True,
        ondelete='cascade',
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        tracking=True
    )
    table_id = fields.Many2one(
        'estate.room.table',
        string="Table Number",
        tracking=True,
        ondelete='restrict'
    )

    table_number = fields.Char(string="Table Number", tracking=True)

    # -------------------------------------------------
    # RELATED FIELDS (FOR EASY FILTERING/GROUPING)
    # -------------------------------------------------
    unit_id = fields.Many2one(related="room_id.hup_unit_id", store=True, tracking=True)
    floor_id = fields.Many2one(related="room_id.hup_floor_id", store=True, tracking=True)
    building_id = fields.Many2one(related="room_id.hup_building_id", store=True, tracking=True)
    property_id = fields.Many2one(related="room_id.hup_property_id", store=True, tracking=True)

    # -------------------------------------------------
    # CREATE OVERRIDE
    # -------------------------------------------------
    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = self.browse()
    #
    #     # context-level cache to prevent double-create
    #     seen = set()
    #
    #     for vals in vals_list:
    #         key = (
    #             vals.get('employee_id'),
    #             vals.get('room_id'),
    #             vals.get('table_id'),
    #         )
    #
    #         # 🛑 block duplicate within same save
    #         if key in seen:
    #             continue
    #         seen.add(key)
    #
    #         existing = self.search([
    #             ('employee_id', '=', vals.get('employee_id')),
    #             ('room_id', '=', vals.get('room_id')),
    #             ('table_id', '=', vals.get('table_id')),
    #         ], limit=1)
    #
    #         if existing:
    #             records |= existing
    #             continue
    #
    #         record = super(EstateRoomEmployee, self).create(vals)
    #         records |= record
    #
    #         record.message_post(
    #             body=_(
    #                 "Employee '%s' assigned to Room '%s' with Table '%s'"
    #             ) % (
    #                      record.employee_id.name,
    #                      record.room_id.name,
    #                      record.table_id.name,
    #                  )
    #         )
    #
    #     return records
    @api.model_create_multi
    def create(self, vals_list):
        records = self.browse()

        for vals in vals_list:


            existing = self.search([
                ('employee_id', '=', vals.get('employee_id')),
                ('room_id', '=', vals.get('room_id')),
                ('table_id', '=', vals.get('table_id')),
            ], limit=1)

            if existing:
                continue

            record = super().create(vals)
            records |= record

        return records

    # -------------------------------------------------
    # WRITE OVERRIDE
    # -------------------------------------------------
    def write(self, vals):

        for rec in self:
            changes = []
            for field, new_value in vals.items():
                old_value = rec[field]
                if old_value != new_value:
                    changes.append(f"<b>{field}</b>: {old_value} → {new_value}")
            if changes:
                message = _("Updated fields:<br/>%s") % "<br/>".join(changes)
                rec.message_post(body=message)

        return super().write(vals)


class EstateRoomTable(models.Model):
    _name = 'estate.room.table'
    _description = 'Room Table Master'
    _inherit = ['mail.thread','mail.activity.mixin',  'estate.hierarchy.mixin','estate.security.mixin','delete.notification.mixin']
    _rec_name = 'name'
    _order = "id desc"

    name = fields.Char(
        string="Table Number",
        required=True,tracking=True
    )
    code = fields.Char(
        string="Code",
        required=True,tracking=True
    )
    code_locked = fields.Boolean(default=False,tracking=True)
    active = fields.Boolean(default=True,tracking=True)

    property_id = fields.Many2one('estate.property', string="Property",tracking=True)
    building_id = fields.Many2one('estate.building', string="Building",tracking=True)
    floor_id = fields.Many2one('estate.floor', string="Floor",tracking=True)
    unit_id = fields.Many2one('estate.unit', string="Unit",tracking=True)
    room_id = fields.Many2one('estate.room', string="Room",tracking=True)

    # 🔼 UPPER
    hup_property_id = fields.Many2one('estate.property', required=True, string="Property",tracking=True)
    hup_building_id = fields.Many2one('estate.building', required=True, string="Building",tracking=True)
    hup_floor_id = fields.Many2one('estate.floor', string="Floors",tracking=True)
    hup_unit_id = fields.Many2one('estate.unit', required=True, string="Units",tracking=True)
    hup_room_id = fields.Many2one('estate.room', required=True, string="Rooms",tracking=True)
    employee_line_ids = fields.One2many(
        'estate.room.employee',
        'table_id',
        string="Employees",tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employees",tracking=True,required=True
    )

    hup_location_id = fields.Many2one(
        'estate.location',
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

    @api.model_create_multi
    def create(self, vals_list):

        # 🔕 Disable default chatter
        self = self.with_context(tracking_disable=True)

        for vals in vals_list:

            # 🚫 Prevent manual prefixed names
            if '/' in (vals.get('name') or ''):
                raise ValidationError(
                    _("Enter only the table number (example: 12). Prefixes are auto-generated.")
                )

            # ✅ USE ONLY HIERARCHY (hup_*)
            building_rec = self.env['estate.building'].browse(vals.get('hup_building_id'))
            floor_rec = self.env['estate.floor'].browse(vals.get('hup_floor_id'))
            unit_rec = self.env['estate.unit'].browse(vals.get('hup_unit_id'))
            room_rec = self.env['estate.room'].browse(vals.get('hup_room_id'))

            building_code = getattr(building_rec, 'building_code', building_rec.display_name) or ''
            floor_code = getattr(floor_rec, 'floor_code', floor_rec.display_name) or ''
            unit_code = getattr(unit_rec, 'unit_code', unit_rec.display_name) or ''
            room_code = room_rec.code or room_rec.display_name or ''

            table_number = vals.get('name')
            table_code = vals.get('code')

            # ✅ FINAL NAME (AS PER YOUR RULE)
            vals['name'] = (
                f"{building_code}/"
                f"{unit_code}/"
                f"{room_code}/"
                f"{table_code}-{table_number}"
            )

            # -------------------------------------------------
            # ✅ ADDED LOGIC (ONLY THIS)
            # Auto-fill flat fields from hierarchy
            # -------------------------------------------------
            if vals.get('hup_room_id') and not vals.get('room_id'):
                vals['room_id'] = vals.get('hup_room_id')

            if vals.get('hup_unit_id') and not vals.get('unit_id'):
                vals['unit_id'] = vals.get('hup_unit_id')

            if vals.get('hup_floor_id') and not vals.get('floor_id'):
                vals['floor_id'] = vals.get('hup_floor_id')

            if vals.get('hup_building_id') and not vals.get('building_id'):
                vals['building_id'] = vals.get('hup_building_id')

            if vals.get('hup_property_id') and not vals.get('property_id'):
                vals['property_id'] = vals.get('hup_property_id')

            # 🔒 Lock code immediately
            # vals['code_locked'] = True

        records = super(EstateRoomTable, self).create(vals_list)

        for record in records:

            if record.employee_id and record.hup_room_id:
                self.env['estate.room.employee'].create({
                    'employee_id': record.employee_id.id,
                    'room_id': record.hup_room_id.id,
                    'table_id': record.id,
                })

            # 🌳 ADD TO HIERARCHY (UNCHANGED LOGIC)
            if record.hup_location_id:
                record._add_to_parent(
                    record.hup_location_id,
                    'hdown_table_ids'
                )
            if record.hup_room_id:
                record._add_to_parent(record.hup_room_id, 'hdown_table_ids')
            if record.hup_unit_id:
                record._add_to_parent(record.hup_unit_id, 'hdown_table_ids')
            if record.hup_floor_id:
                record._add_to_parent(record.hup_floor_id, 'hdown_table_ids')
            if record.hup_building_id:
                record._add_to_parent(record.hup_building_id, 'hdown_table_ids')
            if record.hup_property_id:
                record._add_to_parent(record.hup_property_id, 'hdown_table_ids')

            # 🧾 CHATTER (SAME STYLE)
            record.message_post(
                body=Markup(
                    _("Table created:<br/><b>%s</b>") % record.name
                )
            )

        return records

    # @api.model_create_multi
    # def create(self, vals_list):
    #
    #     # 🔕 Disable default chatter
    #     self = self.with_context(tracking_disable=True)
    #
    #     for vals in vals_list:
    #
    #         # 🚫 Prevent manual prefixed names
    #         if '/' in (vals.get('name') or ''):
    #             raise ValidationError(
    #                 _("Enter only the table number (example: 12). Prefixes are auto-generated.")
    #             )
    #
    #         # ✅ USE ONLY HIERARCHY (hup_*)
    #         building_rec = self.env['estate.building'].browse(vals.get('hup_building_id'))
    #         floor_rec = self.env['estate.floor'].browse(vals.get('hup_floor_id'))
    #         unit_rec = self.env['estate.unit'].browse(vals.get('hup_unit_id'))
    #         room_rec = self.env['estate.room'].browse(vals.get('hup_room_id'))
    #
    #         building_code = getattr(building_rec, 'building_code', building_rec.display_name) or ''
    #         floor_code = getattr(floor_rec, 'floor_code', floor_rec.display_name) or ''
    #         unit_code = getattr(unit_rec, 'unit_code', unit_rec.display_name) or ''
    #         room_code = room_rec.code or room_rec.display_name or ''
    #
    #         table_number = vals.get('name')
    #         table_code = vals.get('code')
    #
    #         # ✅ FINAL NAME (AS PER YOUR RULE)
    #         vals['name'] = (
    #             f"{building_code}/"
    #             # f"{floor_code}/"
    #             f"{unit_code}/"
    #             f"{room_code}/"
    #             f"{table_code}-{table_number}"
    #             # f"{table_code}/"
    #             # f"{table_number}"
    #         )
    #
    #         # 🔒 Lock code immediately
    #         # vals['code_locked'] = True
    #
    #     records = super(EstateRoomTable, self).create(vals_list)
    #
    #     for record in records:
    #
    #         # 🌳 ADD TO HIERARCHY (UNCHANGED LOGIC)
    #         if record.hup_room_id:
    #             record._add_to_parent(record.hup_room_id, 'hdown_table_ids')
    #         if record.hup_unit_id:
    #             record._add_to_parent(record.hup_unit_id, 'hdown_table_ids')
    #         if record.hup_floor_id:
    #             record._add_to_parent(record.hup_floor_id, 'hdown_table_ids')
    #         if record.hup_building_id:
    #             record._add_to_parent(record.hup_building_id, 'hdown_table_ids')
    #         if record.hup_property_id:
    #             record._add_to_parent(record.hup_property_id, 'hdown_table_ids')
    #
    #         # 🧾 CHATTER (SAME STYLE)
    #         record.message_post(
    #             body=Markup(
    #                 _("Table created:<br/><b>%s</b>") % record.name
    #             )
    #         )
    #
    #     return records

    def write(self, vals):

        if 'code' in vals and '/' in (vals.get('code') or ''):
            raise ValidationError(_("Table Code must not contain '/'."))

        # -------------------------------------------------
        # 🔁 AUTO-RENAME WHEN HIERARCHY / TABLE NUMBER CHANGES
        # -------------------------------------------------
        rename_fields = {
            'hup_building_id',
            'hup_floor_id',
            'hup_unit_id',
            'hup_room_id',
            'name',
            'code'  # table number edited
        }

        if rename_fields.intersection(vals.keys()):
            for rec in self:
                building = self.env['estate.building'].browse(
                    vals.get('hup_building_id', rec.hup_building_id.id)
                )
                floor = self.env['estate.floor'].browse(
                    vals.get('hup_floor_id', rec.hup_floor_id.id)
                )
                unit = self.env['estate.unit'].browse(
                    vals.get('hup_unit_id', rec.hup_unit_id.id)
                )
                room = self.env['estate.room'].browse(
                    vals.get('hup_room_id', rec.hup_room_id.id)
                )

                # table_number = vals.get('name', rec.name.split('/')[-1])
                existing_tail = rec.name.split('/')[-1] if rec.name else ''
                existing_number = existing_tail.split('-')[-1] if '-' in existing_tail else existing_tail
                table_number = vals.get('name', existing_number)

                building_code = building.building_code or building.display_name or ''
                floor_code = floor.floor_code or floor.display_name or ''
                unit_code = unit.unit_code or unit.display_name or ''
                room_code = room.code or room.display_name or ''
                table_code = vals.get('code', rec.code)
                vals['name'] = (
                    f"{building_code}/"
                    # f"{floor_code}/"
                    f"{unit_code}/"
                    f"{room_code}/"
                    f"{table_code}-{table_number}"
                )

        # -------------------------------------------------
        # 🧾 PREPARE CHATTER (UNCHANGED LOGIC)
        # -------------------------------------------------
        changes_dict = {}
        for record in self:
            changes = []

            for field_name, new_value in vals.items():

                field = record._fields.get(field_name)
                if not field:
                    continue
                if field.type in ('one2many', 'many2many', 'html', 'binary'):
                    continue

                old_value = record[field_name]

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
        res = super(EstateRoomTable, self.with_context(tracking_disable=True)).write(vals)

        # 🧾 POST CHATTER
        for record in self:
            if record.id in changes_dict:
                record.message_post(
                    body=Markup(
                        _("Updated fields:<br/>%s") % changes_dict[record.id]
                    )
                )

        return res
