from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class HelpdeskDepartment(models.Model):
    _name = 'helpdesk.department'
    _description = 'Helpdesk Department'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char()
    manager_id = fields.Many2one('res.users', string="Manager", required=True, tracking=True)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    requested_department_id = fields.Many2one(
        "hr.department",
        string="Requested Department",
        related="user_id.employee_id.department_id",
        store=True,
        readonly=True, tracking=True
    )
    description = fields.Text(string="Description", help="Enter detailed description", tracking=True)
    manager_id_main = fields.Many2one(
        'res.users',
        string="Manager",
        compute="_compute_manager",
        store="True", tracking=True
    )

    name = fields.Char(required=True, tracking=True)
    description = fields.Text()
    user_id = fields.Many2one('res.users', string="Owner", default=lambda self: self.env.user, tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", tracking=True)

    before_photo_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_before_rel',
        'ticket_id',
        'attachment_id',
        string="Before Photos", tracking=True
    )

    after_photo_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_after_rel',
        'ticket_id',
        'attachment_id',
        string="After Photos", tracking=True
    )

    photo_count = fields.Integer(
        string="Photos",
        compute="_compute_photo_count", tracking=True
    )

    @api.depends('before_photo_ids', 'after_photo_ids')
    def _compute_photo_count(self):
        for rec in self:
            rec.photo_count = len(rec.before_photo_ids) + len(rec.after_photo_ids)

    def action_view_photos(self):
        self.ensure_one()
        attachments = self.before_photo_ids | self.after_photo_ids

        return {
            'type': 'ir.actions.act_window',
            'name': 'All Photos',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,form',
            'domain': [('id', 'in', attachments.ids)]
        }

    type_id = fields.Many2one(
        "helpdesk.ticket.type",
        string="Ticket Type",
        invisible=True, tracking=True
    )

    time_remaining = fields.Char(
        string="Time Remaining",
        compute="_compute_time_remaining", tracking=True
    )

    time_status = fields.Selection(
        [
            ('ok', 'On Time'),
            ('near', 'Near Deadline'),
            ('late', 'Overdue')
        ],
        compute="_compute_time_remaining", tracking=True
    )

    @api.depends('deadline', 'closed')
    def _compute_time_remaining(self):

        now = fields.Datetime.now()

        for record in self:

            # ✅ STOP when ticket is closed
            if record.closed:
                record.time_remaining = False
                record.time_status = False
                continue

            if not record.deadline:
                record.time_remaining = False
                record.time_status = False
                continue

            deadline_dt = fields.Datetime.to_datetime(record.deadline)
            deadline_dt = deadline_dt.replace(hour=23, minute=59, second=59)

            diff = deadline_dt - now
            hours = diff.total_seconds() / 3600
            days = diff.days

            if hours > 48:
                record.time_remaining = f"{int(hours)} hrs left"
                record.time_status = 'ok'

            elif 34 <= hours <= 48:
                record.time_remaining = f"{int(hours)} hrs left"
                record.time_status = 'near'

            elif 0 < hours < 34:
                record.time_remaining = f"{int(hours)} hrs left"
                record.time_status = 'late'

            else:
                overdue_days = abs(days)

                if overdue_days == 1:
                    record.time_remaining = "1 day overdue"
                else:
                    record.time_remaining = f"{overdue_days} days overdue"

                record.time_status = 'late'

    deadline = fields.Date(string="Deadline", tracking=True)

    sla_due_date = fields.Date(
        string="SLA Due Date",
        related="deadline",
        store=True, tracking=True
    )

    sla_risk = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red')
        ],
        compute="_compute_backlog_sla",
        store=True, tracking=True,
    )

    sla_state = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red')
        ],
        compute="_compute_backlog_sla",
        store=True, tracking=True,
    )

    sla_stage = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red'),
            ('red_3', 'Overdue +3 Days'),
            ('red_6', 'Overdue +6 Days'),
        ],
        compute="_compute_backlog_sla",
        store=True, tracking=True,
    )

    sla_days_remaining = fields.Integer(
        compute="_compute_backlog_sla",
        store=True, tracking=True,
    )

    sla_days_label = fields.Char(
        string="SLA Days",
        compute="_compute_sla_days_label",
        store=True, tracking=True,
    )

    sla_escalation_rules = fields.Text(
        string="SLA Escalation Rules", tracking=True,
    )

    # =========================
    # ESCALATION USERS
    # =========================

    # sla_amber_user_ids = fields.Many2many(
    #     'res.users',
    #     'project_sla_amber_rel',
    #     'project_id',
    #     'user_id',
    #     string="Amber Escalation Owners"
    # )
    #
    # sla_red_user_ids = fields.Many2many(
    #     'res.users',
    #     'project_sla_red_rel',
    #     'project_id',
    #     'user_id',
    #     string="Red Escalation Owners"
    # )
    #
    # sla_overdue_3_user_ids = fields.Many2many(
    #     'res.users',
    #     'project_sla_overdue3_rel',
    #     'project_id',
    #     'user_id',
    #     string="Overdue +3 Days Owners"
    # )
    #
    # sla_overdue_6_user_ids = fields.Many2many(
    #     'res.users',
    #     'project_sla_overdue6_rel',
    #     'project_id',
    #     'user_id',
    #     string="Overdue +6 Days Owners"
    # )
    sla_amber_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_ticket_sla_amber_rel',
        'ticket_id',
        'user_id',
        string="Amber Escalation Owners", tracking=True
    )

    sla_red_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_ticket_sla_red_rel',
        'ticket_id',
        'user_id',
        string="Red Escalation Owners", tracking=True
    )

    sla_overdue_3_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_ticket_sla_overdue3_rel',
        'ticket_id',
        'user_id',
        string="Overdue +3 Days Owners", tracking=True
    )

    sla_overdue_6_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_ticket_sla_overdue6_rel',
        'ticket_id',
        'user_id',
        string="Overdue +6 Days Owners", tracking=True
    )

    # =========================
    # DATES
    # =========================

    is_done = fields.Boolean(string="Is Completed", default=False, tracking=True)

    planned_start_date = fields.Date(string="Planned Start Date", tracking=True)
    planned_end_date = fields.Date(string="Planned End Date", tracking=True)

    assign_to = fields.Many2one(
        'res.users',
        string="Assign To",
        tracking=True
    )

    assign_date = fields.Datetime(
        string="Assign Date",
        readonly=True,
        copy=False,
        tracking=True
    )

    resolved_date = fields.Datetime(
        string="Resolved Date",
        readonly=True,
        copy=False,
        tracking=True
    )

    completed_date = fields.Datetime(
        string="Closing Date",
        readonly=True,
        copy=False,
        tracking=True
    )

    @api.model
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('assign_to'):
                vals['assign_date'] = fields.Datetime.now()
                vals['user_id'] = vals.get('assign_to')  # IMPORTANT
        return super().create(vals_list)

    def write(self, vals):

        # Assign Date
        if 'assign_to' in vals:
            vals['assign_date'] = fields.Datetime.now()
            vals['user_id'] = vals.get('assign_to')

        # Stage Change
        if 'stage_id' in vals:
            new_stage = self.env['helpdesk.ticket.stage'].browse(vals['stage_id'])
            done_stage = self.env.ref('helpdesk_mgmt.helpdesk_ticket_stage_done')

            # ADD THIS LINE
            resolved_stage = self.env['helpdesk.ticket.stage'].search([('name', '=', 'Resolved')], limit=1)

            for rec in self:

                # ADD THIS BLOCK
                if new_stage.id == resolved_stage.id:

                    is_manager = self.env.user.has_group(
                        'department_helpdesk.group_helpdesk_department_manager'
                    )

                    is_assigned_user = rec.assign_to.id == self.env.user.id

                    if not (is_manager or is_assigned_user):
                        raise UserError(
                            "Only the assigned user or Department Manager can resolve this ticket."
                        )

                # Only Department Manager can mark Done
                if new_stage.id == done_stage.id:
                    if not self.env.user.has_group('department_helpdesk.group_helpdesk_department_manager'):
                        raise UserError("Only Department Manager can mark the ticket as Done.")

                # Resolved Date
                if new_stage.name == "Resolved" and not rec.resolved_date:
                    vals['resolved_date'] = fields.Datetime.now()

                # Completed Date
                if new_stage.closed and not rec.completed_date:
                    vals['completed_date'] = fields.Datetime.now()

        return super().write(vals)

    tat_ticket = fields.Float(
        string="TAT of Ticket (Hours)",
        compute="_compute_tat_ticket",
        store=True, tracking=True
    )

    tat_assignment = fields.Float(
        string="TAT of Assignment (Hours)",
        compute="_compute_tat_assignment",
        store=True, tracking=True
    )

    # TAT Ticket = Request Date → Close Date
    @api.depends('requested_date', 'completed_date')
    def _compute_tat_ticket(self):
        for rec in self:
            if rec.requested_date and rec.completed_date:
                delta = rec.completed_date - rec.requested_date
                rec.tat_ticket = delta.total_seconds() / 3600.0
            else:
                rec.tat_ticket = 0.0

    # TAT Assignment = Assign Date → Resolved Date
    @api.depends('assign_date', 'resolved_date')
    def _compute_tat_assignment(self):
        for rec in self:
            if rec.assign_date and rec.resolved_date:
                delta = rec.resolved_date - rec.assign_date
                rec.tat_assignment = delta.total_seconds() / 3600.0
            else:
                rec.tat_assignment = 0.0

    # =========================
    # LABEL COMPUTE
    # =========================

    @api.depends('sla_days_remaining', 'closed')
    def _compute_sla_days_label(self):
        for rec in self:

            # ✅ If ticket closed → show nothing
            if rec.closed:
                rec.sla_days_label = False
                continue

            days = rec.sla_days_remaining

            if days > 0:
                rec.sla_days_label = f"{days} days remaining"
            elif days == 0:
                rec.sla_days_label = "Due today"
            else:
                rec.sla_days_label = f"{abs(days)} days overdue"

    def _get_parent_field(self):
        return False

    # =========================
    # SLA CALCULATION
    # =========================
    @api.depends('deadline', 'closed')
    def _compute_backlog_sla(self):

        now = fields.Datetime.now()

        for rec in self:

            # ✅ If ticket closed → CLEAR everything
            if rec.closed:
                rec.sla_stage = False
                rec.sla_risk = False
                rec.sla_state = False
                rec.sla_days_remaining = 0
                continue

            if not rec.deadline:
                rec.sla_stage = False
                rec.sla_risk = False
                rec.sla_state = False
                rec.sla_days_remaining = 0
                continue

            deadline_dt = fields.Datetime.to_datetime(rec.deadline)
            deadline_dt = deadline_dt.replace(hour=23, minute=59, second=59)

            diff = deadline_dt - now
            hours = diff.total_seconds() / 3600
            days = diff.days

            rec.sla_days_remaining = days

            if hours > 48:
                stage = 'green'
            elif 0 < hours < 24:
                stage = 'red'
            elif 24 <= hours <= 48:
                stage = 'amber'
            elif -3 <= days < 0:
                stage = 'red'
            elif -6 <= days < -3:
                stage = 'red_3'
            else:
                stage = 'red_6'

            rec.sla_stage = stage
            rec.sla_risk = 'red' if stage.startswith('red') else stage
            rec.sla_state = rec.sla_risk

    # =========================
    # ACTION BUTTONS
    # =========================

    def action_open_story_sla_7_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=7)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Stories - Next 7 Days',
            'res_model': 'product.backlog',
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
        }

    def action_open_story_sla_30_days(self):
        self.ensure_one()

        today = fields.Date.today()
        limit_date = today + timedelta(days=30)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Upcoming Stories - Next 30 Days',
            'res_model': 'product.backlog',
            'view_mode': 'list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('planned_end_date', '>=', today),
                ('planned_end_date', '<=', limit_date),
                ('is_done', '=', False),
            ],
        }

    def action_open_sla_monitoring(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'SLA Monitoring',
            'res_model': 'product.backlog',
            'view_mode': 'kanban,list,form',
            'domain': [
                ('project_id', '=', self.id),
                ('is_done', '=', False),
            ],
            'context': {
                'group_by': 'sla_stage',
            },
        }

    urgency_id = fields.Many2one(
        'helpdesk.urgency',
        string='Urgency', tracking=True
    )

    impact_id = fields.Many2one(
        'helpdesk.impact',
        string='Impact', tracking=True
    )

    priority_master_id = fields.Many2one(
        'helpdesk.priority.master',
        string='Priority Master', tracking=True
    )
    resolved_date = fields.Datetime(string="Resolved Date", tracking=True)
    close_date = fields.Datetime(string="Close Date", tracking=True)

    attachments_permit = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_permit_attachment_rel',
        'ticket_id',
        'attachment_id',
        string="Permit Attachments", tracking=True
    )

    parts_required_ids = fields.One2many(
        'helpdesk.parts.required',
        'ticket_id',
        string="Parts Required", tracking=True
    )

    parts_issued_ids = fields.One2many(
        'helpdesk.parts.issued',
        'ticket_id',
        string="Parts Issued", tracking=True
    )

    labor_hours = fields.Float(string="Labor Hours", tracking=True)

    material_cost = fields.Monetary(string="Material Cost", tracking=True)
    labor_cost = fields.Monetary(string="Labor Cost", tracking=True)
    other_cost = fields.Monetary(string="Other Cost", tracking=True)

    total_cost = fields.Monetary(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True, tracking=True
    )

    resolution_notes = fields.Html(string="Resolution Notes", tracking=True)

    # before_photos = fields.Many2many(
    #     'helpdesk.before.photo.master',
    #     string="Before Photos"
    # )
    #
    # after_photos = fields.Many2many(
    #     'helpdesk.after.photo.master',
    #     string="After Photos"
    # )
    # #
    # def action_before_photos(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Before Photos',
    #         'res_model': 'ir.attachment',
    #         'view_mode': 'kanban',  # ✅ Only kanban
    #         'domain': [
    #             ('res_model', '=', 'helpdesk.ticket'),
    #             ('res_id', '=', self.id),
    #             ('description', '=', 'before_photo')
    #         ],
    #         'context': {
    #             'default_res_model': 'helpdesk.ticket',
    #             'default_res_id': self.id,
    #             'default_description': 'before_photo',
    #         }
    #     }
    #
    # def action_after_photos(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'After Photos',
    #         'res_model': 'ir.attachment',
    #         'view_mode': 'kanban',  # ✅ Only kanban
    #         'domain': [
    #             ('res_model', '=', 'helpdesk.ticket'),
    #             ('res_id', '=', self.id),
    #             ('description', '=', 'after_photo')
    #         ],
    #         'context': {
    #             'default_res_model': 'helpdesk.ticket',
    #             'default_res_id': self.id,
    #             'default_description': 'after_photo',
    #         }
    #     }

    signoff_by = fields.Many2one(
        'res.users',
        string="Signed Off By", tracking=True
    )

    signoff_at = fields.Datetime(string="Signed Off At", tracking=True)

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id.id
    )

    target_start_at = fields.Datetime(string="Target Start", tracking=True)
    target_end_at = fields.Datetime(string="Target End", tracking=True)
    preferred_window = fields.Text(string="Preferred Window", tracking=True)

    downtime_expected = fields.Boolean(string="Downtime Expected", tracking=True)

    downtime_start = fields.Datetime(string="Downtime Start", tracking=True)
    downtime_end = fields.Datetime(string="Downtime End", tracking=True)

    # =====================================
    # LOCATION FIELDS
    # =====================================

    property_name = fields.Char(string="Property", tracking=True)
    building_name = fields.Char(string="Building", tracking=True)
    floor_name = fields.Char(string="Floor", tracking=True)
    unit_name = fields.Char(string="Unit", tracking=True)
    room_name = fields.Char(string="Room", tracking=True)
    table_name = fields.Char(string="Table", tracking=True)

    hup_property_id = fields.Many2one('estate.property', tracking=True)
    hup_building_id = fields.Many2one('estate.building', tracking=True)
    hup_floor_id = fields.Many2one('estate.floor', tracking=True)
    hup_unit_id = fields.Many2one('estate.unit', tracking=True)
    hup_room_id = fields.Many2one('estate.room', tracking=True)
    asset_inventory_id = fields.Many2one(
        'custom.inventory',
        string="Asset Tag",
        domain="[('asset_tag','!=',False)]"
    )
    asset_type_id = fields.Many2one('inventory.asset.type', string="Asset Type", tracking=True)
    asset_category_id = fields.Many2one('inventory.asset.category', string="Asset Category", tracking=True)
    product_name_id = fields.Many2one('inventory.product', string="Product Name", tracking=True)
    brand_id = fields.Many2one('inventory.brand', string="Brand", tracking=True)
    model_id = fields.Many2one('inventory.model', string="Model", tracking=True)
    serial_no = fields.Char(string="Serial Number", tracking=True)
    warehouse_id = fields.Many2one('inventory.warehouse', string="Warehouse", tracking=True)
    asset_owner_id = fields.Many2one('hr.employee', string="Asset Owner", tracking=True)

    @api.onchange('asset_inventory_id')
    def _onchange_asset_inventory(self):
        for rec in self:

            if not rec.asset_inventory_id:
                rec.asset_type_id = False
                rec.asset_category_id = False
                rec.product_name_id = False
                rec.brand_id = False
                rec.model_id = False
                rec.serial_no = False
                rec.warehouse_id = False
                rec.asset_owner_id = False
                return

            asset = rec.asset_inventory_id

            rec.asset_type_id = asset.asset_type_id.id
            rec.asset_category_id = asset.asset_category_id.id
            rec.product_name_id = asset.product_name_id.id
            rec.brand_id = asset.brand_id.id
            rec.model_id = asset.model_id.id
            rec.serial_no = asset.serial_no
            rec.warehouse_id = asset.warehouse_id.id
            rec.asset_owner_id = asset.asset_owner.id

            # Also fetch location automatically
            rec.hup_property_id = asset.property_id.id
            rec.hup_building_id = asset.building_id.id
            rec.hup_floor_id = asset.floor_id.id
            rec.hup_unit_id = asset.unit_id.id
            rec.hup_room_id = asset.room_id.id

    # ============================
    # REQUEST DETAILS
    # ============================

    request_title = fields.Char(string="Request Title", tracking=True)

    requested_date = fields.Datetime(
        string="Requested Date",
        default=fields.Datetime.now, tracking=True
    )

    requested_person_id = fields.Many2one(
        "res.users",
        string="Requested Person",
        default=lambda self: self.env.user,
        readonly=True, tracking=True
    )

    req_department_id = fields.Many2one(
        related='requested_person_id.employee_id.department_id',
        string="Requested Department",
        store=True,
        readonly=True, tracking=True
    )

    # @api.depends('requested_person_id')
    # def _compute_department(self):
    #     for rec in self:
    #         rec.department_id = False
    #         employee = self.env.user.employee_id
    #         if employee and employee.department_id:
    #             rec.department_id = employee.department_id.id

    # requested_source = fields.Selection([
    #     ('web', 'Web'),
    #     ('email', 'Email'),
    #     ('phone', 'Phone'),
    #     ('portal', 'Portal'),
    #     ('internal', 'Internal'),
    # ], string="Requested Source")

    # ============================
    # Department
    # ============================

    # department_id = fields.Many2one(
    #     'helpdesk.department',
    #     string="Department",
    #     ondelete='cascade', tracking=True
    # )

    # ============================
    # LOCATION
    # ============================

    property_name = fields.Char(string="Property")
    # property_id = fields.Char(string="Property_id")
    building_name = fields.Char(string="Building")
    unit_name = fields.Char(string="Unit / Floor")
    room_name = fields.Char(string="Room")
    location_code = fields.Char(string="Location Code")

    target_start_at = fields.Datetime(
        string="Target Start", tracking=True
    )

    target_end_at = fields.Datetime(
        string="Target End", tracking=True
    )

    preferred_window = fields.Text(
        string="Preferred Time Window", tracking=True
    )

    downtime_expected = fields.Boolean(
        string="Downtime Expected", tracking=True
    )

    downtime_start = fields.Datetime(
        string="Downtime Start", tracking=True
    )

    downtime_end = fields.Datetime(
        string="Downtime End", tracking=True)
    # ============================
    # VENDOR & COMPLIANCE
    # ============================

    external_vendor_id = fields.Many2one(
        'res.partner',
        string="External Vendor",
        domain="[('supplier_rank', '>', 0)]", tracking=True
    )

    vendor_contact = fields.Char(
        string="Vendor Contact"
    )

    contract_id = fields.Many2one(
        'facility.contract',
        string="AMC / Maintenance Contract", tracking=True
    )

    permit_required = fields.Boolean(
        string="Permit Required", tracking=True
    )

    permit_id = fields.Many2one(
        'facility.permit',
        string="Work Permit", tracking=True
    )

    safety_checklist_completed = fields.Boolean(
        string="Safety Checklist Completed", tracking=True
    )

    attachments_permit = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_permit_attachment_rel',
        'ticket_id',
        'attachment_id',
        string="Permit Attachments", tracking=True
    )

    # ============================
    # MAINTENANCE
    # ============================

    geo_coords = fields.Selection([
        ('lat', 'Latitude'),
        ('long', 'Longitude')
    ], string="Geo Coordinate Type", tracking=True)

    geo_value = fields.Float(string="Coordinate Value")

    trade_id = fields.Many2one(
        'helpdesk.trade',
        string="Trade", tracking=True
    )
    issue_type = fields.Selection([
        # Electrical
        ('short_circuit', 'Short Circuit'),
        ('power_failure', 'Power Failure'),
        ('light_not_working', 'Light Not Working'),

        # Plumbing
        ('water_leakage', 'Water Leakage'),
        ('pipe_blockage', 'Pipe Blockage'),
        ('low_water_pressure', 'Low Water Pressure'),

        # HVAC
        ('ac_not_cooling', 'AC Not Cooling'),
        ('noise_issue', 'Abnormal Noise'),
        ('filter_dirty', 'Filter Dirty'),

        # Civil
        ('wall_crack', 'Wall Crack'),
        ('ceiling_damage', 'Ceiling Damage'),

        # Fire & Safety
        ('fire_alarm_fault', 'Fire Alarm Fault'),
        ('extinguisher_expired', 'Fire Extinguisher Expired'),

        # Security
        ('camera_not_working', 'Camera Not Working'),
        ('access_card_issue', 'Access Card Issue'),
    ], string="Issue Type / Fault Code", tracking=True)

    maintenance_type_id = fields.Many2one(
        'maintenance.type',
        string="Maintenance Type", tracking=True
    )

    severity_id = fields.Many2one(
        'maintenance.severity',
        string="Severity", tracking=True
    )

    impact_level = fields.Selection([
        ('low', 'Low Impact'),
        ('medium', 'Medium Impact'),
        ('high', 'High Impact')
    ], string="Impact Level", tracking=True)

    # =====================================
    # EQUIPMENT / FACILITY OBJECTS
    # =====================================

    facility_asset_id = fields.Many2one(
        'facility.asset',
        string="Facility Asset", tracking=True
    )

    asset_serial = fields.Char(string="Asset Serial")

    warranty_start_date = fields.Date(
        string="Warranty Start", tracking=True
    )

    warranty_end_date = fields.Date(
        string="Warranty End", tracking=True
    )

    warranty_status = fields.Selection([
        ('in', 'In Warranty'),
        ('out', 'Out of Warranty')
    ], string="Warranty Status",
        compute="_compute_warranty_status",
        store=True, tracking=True)

    @api.depends('warranty_end_date')
    def _compute_warranty_status(self):
        today = date.today()
        for rec in self:
            if rec.warranty_end_date and rec.warranty_end_date >= today:
                rec.warranty_status = 'in'
            else:
                rec.warranty_status = 'out'

    # ============================
    # COSTING
    # ============================

    material_cost = fields.Float(string="Material Cost", tracking=True)
    labor_cost = fields.Float(string="Labor Cost", tracking=True)
    other_cost = fields.Float(string="Other Cost", tracking=True)

    total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True, tracking=True
    )
    manager_id = fields.Many2one(
        "hr.employee",
        string="Manager",
        compute="_compute_manager",
        store=True,
        readonly=True, tracking=True
    )
    department_id_main = fields.Many2one(
        'helpdesk.department',
        string="Department", tracking=True
    )
    department_name = fields.Char(
        compute="_compute_department_name",
        store=False, tracking=True
    )

    @api.depends('department_id_main')
    def _compute_department_name(self):
        for rec in self:
            rec.department_name = rec.department_id_main.name if rec.department_id_main else False

    @api.depends('department_id_main')
    def _compute_manager(self):
        for rec in self:
            rec.manager_id_main = rec.department_id_main.manager_id.id if rec.department_id_main else False

    # ============================
    # PERMIT
    # ============================

    permit_required = fields.Boolean(string="Permit Required", tracking=True)
    permit_reference = fields.Char(string="Permit Reference", tracking=True)

    # ============================
    # COMPUTE
    # ============================

    @api.depends('material_cost', 'labor_cost', 'other_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (
                    (rec.material_cost or 0.0) +
                    (rec.labor_cost or 0.0) +
                    (rec.other_cost or 0.0)
            )

    # ============================
    # VALIDATIONS
    # ============================

    @api.constrains('room_name', 'location_code')
    def _check_location(self):
        for rec in self:
            if rec.department_id and rec.department_id.name == 'Facility':
                if not (rec.room_name or rec.location_code):
                    raise ValidationError(
                        "Provide Room or Location for Facility tickets."
                    )

    @api.constrains('permit_required', 'permit_reference')
    def _check_permit(self):
        for rec in self:
            if rec.department_id and rec.department_id.name == 'Facility':
                if rec.permit_required and not rec.permit_reference:
                    raise ValidationError(
                        "Permit reference required."
                    )

    permit_required = fields.Boolean(string="Permit Required", tracking=True)
    permit_id = fields.Many2one('facility.permit', tracking=True)
    safety_checklist_completed = fields.Boolean()

    @api.constrains('permit_required', 'permit_id', 'safety_checklist_completed')
    def _check_permit_requirements(self):
        for rec in self:
            if rec.permit_required:
                if not rec.permit_id:
                    raise ValidationError("Permit must be selected.")
                if not rec.safety_checklist_completed:
                    raise ValidationError("Safety checklist must be completed.")

    # =====================================
    # PARTS
    # =====================================
    #
    # parts_required_ids = fields.One2many(
    #     'helpdesk.ticket.part',
    #     'ticket_id',
    #     string="Parts Required",
    #     domain=[('part_type', '=', 'required')]
    # )
    #
    # parts_issued_ids = fields.One2many(
    #     'helpdesk.ticket.part',
    #     'ticket_id',
    #     string="Parts Issued",
    #     domain=[('part_type', '=', 'issued')]
    # )

    # =====================================
    # COSTING
    # =====================================

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id, tracking=True
    )

    labor_hours = fields.Float(string="Labor Hours", tracking=True)

    material_cost = fields.Monetary(string="Material Cost", tracking=True)
    labor_cost = fields.Monetary(string="Labor Cost", tracking=True)
    other_cost = fields.Monetary(string="Other Cost", tracking=True)

    total_cost = fields.Monetary(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True, tracking=True
    )

    @api.depends('material_cost', 'labor_cost', 'other_cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = (
                    (rec.material_cost or 0.0) +
                    (rec.labor_cost or 0.0) +
                    (rec.other_cost or 0.0)
            )

    # =====================================
    # CLOSEOUT
    # =====================================

    resolution_notes = fields.Html(string="Resolution Notes", tracking=True)

    # before_photos = fields.Image(string="Before Photos")
    # after_photos = fields.Image(string="After Photos")

    signoff_by = fields.Many2one(
        'res.users',
        string="Signed Off By", tracking=True
    )

    signoff_at = fields.Datetime(string="Signed Off At", tracking=True)

    @api.onchange('requested_person_id')
    def _onchange_requested_person_location(self):
        for rec in self:

            if not rec.requested_person_id:
                rec.property_name = False
                rec.building_name = False
                rec.floor_name = False
                rec.unit_name = False
                rec.room_name = False
                rec.table_name = False
                return

            # Convert User → Employee
            employee = self.env['hr.employee'].search([
                ('user_id', '=', rec.requested_person_id.id)
            ], limit=1)

            if not employee:
                return

            # Find table assigned to employee
            room_employee = self.env['estate.room.employee'].search([
                ('employee_id', '=', employee.id)
            ], limit=1)

            if room_employee and room_employee.table_id:
                table = room_employee.table_id

                rec.property_name = table.hup_property_id.name or ''
                rec.building_name = table.hup_building_id.name or ''
                rec.floor_name = table.hup_floor_id.name or ''
                rec.unit_name = table.hup_unit_id.name or ''
                rec.room_name = table.hup_room_id.name or ''
                rec.table_name = table.name or ''


class MaintenanceType(models.Model):
    _name = 'maintenance.type'
    _description = 'Maintenance Type'
    _order = 'sequence, name'

    name = fields.Char(string="Name", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class MaintenanceSeverity(models.Model):
    _name = 'maintenance.severity'
    _description = 'Maintenance Severity'
    _order = 'sequence, name'

    name = fields.Char(string="Name", required=True, tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class RequestType(models.Model):
    _name = 'request.type'
    _description = 'Request Type'
    _order = 'name'

    request_type_id = fields.Many2one(
        'request.type',
        string="Request Type", tracking=True
    )

    name = fields.Char(string="Request Type", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    priority = fields.Integer(string="Priority", tracking=True)


class HelpdeskTrade(models.Model):
    _name = 'helpdesk.trade'
    _description = 'Trade Master'
    _order = 'name'

    name = fields.Char(string="Trade Name", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class HelpdeskPartsRequired(models.Model):
    _name = 'helpdesk.parts.required'
    _description = 'Parts Required'

    ticket_id = fields.Many2one('helpdesk.ticket', ondelete='cascade', tracking=True)
    product_id = fields.Many2one('product.product', string="Parts Required Item", required=True, tracking=True)
    qty = fields.Float(string="Quantity", tracking=True)
    uom_id = fields.Many2one('uom.uom', string="UoM", tracking=True)


class HelpdeskPartsIssued(models.Model):
    _name = 'helpdesk.parts.issued'
    _description = 'Parts Issued'

    ticket_id = fields.Many2one('helpdesk.ticket', ondelete='cascade', tracking=True)
    product_id = fields.Many2one('product.product', string="Parts issued Item", required=True, tracking=True)
    qty = fields.Float(string="Quantity", tracking=True)
    uom_id = fields.Many2one('uom.uom', string="UoM", tracking=True)


class HelpdeskUrgency(models.Model):
    _name = 'helpdesk.urgency'
    _description = 'Helpdesk Urgency'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class HelpdeskImpact(models.Model):
    _name = 'helpdesk.impact'
    _description = 'Helpdesk Impact'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class HelpdeskPriority(models.Model):
    _name = 'helpdesk.priority.master'
    _description = 'Helpdesk Priority Master'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
#
# class IrAttachment(models.Model):
#     _inherit = "ir.attachment"
#
#     photo_type = fields.Selection([
#         ('before','Before'),
#         ('after','After')
#     ])

# class HelpdeskBeforephoto(models.Model):
#     _name = 'helpdesk.before.photo.master'
#     _description = 'Helpdesk Before photo Master'
#
#     name = fields.Char(required=True)
#     sequence = fields.Integer(default=10)
#     active = fields.Boolean(default=True)
#
# class HelpdeskAfterphoto(models.Model):
#     _name = 'helpdesk.after.photo.master'
#     _description = 'Helpdesk After photo Master'
#
#     name = fields.Char(required=True)
#     sequence = fields.Integer(default=10)
#     active = fields.Boolean(default=True)
