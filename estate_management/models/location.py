from odoo import models, fields, api, _
# from markupsafe import Markup, escape

class EstateLocation(models.Model):
    _name = 'estate.location'
    _inherit = ['mail.thread', 'estate.hierarchy.mixin','estate.security.mixin','delete.notification.mixin']
    _description = 'Location'
    _rec_name = 'name'
    _order = "id desc"

    # ========================
    # BASIC INFO
    # ========================
    name = fields.Char(string="Location Name", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # ========================
    # 🔽 DOWN HIERARCHY
    # ========================

    hdown_property_ids = fields.Many2many(
        'estate.property',
        string="Properties",tracking=True
    )

    hdown_building_ids = fields.Many2many(
        'estate.building',
        string="Buildings",tracking=True
    )

    hdown_floor_ids = fields.Many2many(
        'estate.floor',
        string="Floors",tracking=True
    )

    hdown_unit_ids = fields.Many2many(
        'estate.unit',
        string="Units",tracking=True
    )

    hdown_room_ids = fields.Many2many(
        'estate.room',
        string="Rooms",tracking=True
    )

    hdown_table_ids = fields.Many2many(
        'estate.room.table',
        string="Tables",tracking=True
    )

    hdown_farm_ids = fields.Many2many(
        'estate.farm',
        string="Farms",tracking=True
    )

    # ========================
    # 🔢 COUNTS
    # ========================

    hcount_property = fields.Integer(compute='_compute_hcounts', string="Properties",tracking=True)
    hcount_building = fields.Integer(compute='_compute_hcounts', string="Buildings",tracking=True)
    hcount_floor = fields.Integer(compute='_compute_hcounts', string="Floors",tracking=True)
    hcount_unit = fields.Integer(compute='_compute_hcounts', string="Units",tracking=True)
    hcount_room = fields.Integer(compute='_compute_hcounts', string="Rooms",tracking=True)
    hcount_table = fields.Integer(compute='_compute_hcounts', string="Tables",tracking=True)
    hcount_farm = fields.Integer(compute='_compute_hcounts', string="Farms",tracking=True)

    @api.depends(
        'hdown_property_ids',
        'hdown_building_ids',
        'hdown_floor_ids',
        'hdown_unit_ids',
        'hdown_room_ids',
        'hdown_table_ids',
        'hdown_farm_ids',
    )
    def _compute_hcounts(self):
        for rec in self:
            rec.hcount_property = len(rec.hdown_property_ids)
            rec.hcount_building = len(rec.hdown_building_ids)
            rec.hcount_floor = len(rec.hdown_floor_ids)
            rec.hcount_unit = len(rec.hdown_unit_ids)
            rec.hcount_room = len(rec.hdown_room_ids)
            rec.hcount_table = len(rec.hdown_table_ids)
            rec.hcount_farm = len(rec.hdown_farm_ids)

    # ========================
    # 🔘 SMART BUTTON ACTIONS
    # ========================

    def haction_open_properties(self):
        return self._open_hdown(
            'Properties',
            'estate.property',
            self.hdown_property_ids,
            {'default_hup_location_id': self.id}
        )

    def haction_open_buildings(self):
        return self._open_hdown(
            'Buildings',
            'estate.building',
            self.hdown_building_ids,
            {'default_hup_location_id': self.id}
        )

    def haction_open_floors(self):
        return self._open_hdown(
            'Floors',
            'estate.floor',
            self.hdown_floor_ids,
            {'default_hup_location_id': self.id}
        )

    def haction_open_units(self):
        return self._open_hdown(
            'Units',
            'estate.unit',
            self.hdown_unit_ids,
            {'default_hup_location_id': self.id}
        )

    def haction_open_rooms(self):
        return self._open_hdown(
            'Rooms',
            'estate.room',
            self.hdown_room_ids,
            {'default_hup_location_id': self.id}
        )

    def haction_open_tables(self):
        return self._open_hdown(
            'Tables',
            'estate.room.table',
            self.hdown_table_ids,
            {'default_hup_location_id': self.id}
        )

    def haction_open_farms(self):
        return self._open_hdown(
            'Farms',
            'estate.farm',
            self.hdown_farm_ids,
            {'default_hup_location_id': self.id}
        )


#
# class MailThread(models.AbstractModel):
#     _inherit = 'mail.thread'
#
#     def message_post(self, **kwargs):
#         body = kwargs.get('body')
#         subtype = kwargs.get('subtype_xmlid')
#
#         print("\n========== LOG NOTE DEBUG START ==========")
#         print("Model:", self._name)
#         print("Record ID:", self.id)
#         print("Subtype:", subtype)
#         print("\n--- ORIGINAL BODY ---\n", body)
#
#         if subtype == 'mail.mt_note' and body:
#             escaped_body = escape(body)
#             safe_body = Markup(f"<pre>{escaped_body}</pre>")
#
#             kwargs['body'] = safe_body
#
#             print("\n--- ESCAPED BODY ---\n", escaped_body)
#             print("\n--- FINAL BODY SENT TO ODOO ---\n", safe_body)
#         else:
#             print("\n--- NO TRANSFORMATION APPLIED ---")
#
#         print("========== LOG NOTE DEBUG END ==========\n")
#
#         return super().message_post(**kwargs)



