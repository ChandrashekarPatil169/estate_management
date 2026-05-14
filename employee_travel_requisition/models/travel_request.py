from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)


class TravelExpenseAccount(models.Model):
    _name = 'travel.expense.account'
    _description = 'Travel Expense Account'
    _order = 'name'

    name = fields.Char(string="Account Name", required=True)
    code = fields.Char(string="Account Code")
    active = fields.Boolean(default=True)


class TravelRequest(models.Model):
    _name = 'travel.request'
    _description = 'Employee Travel Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    # --------------------------
    # Basic Information
    # --------------------------

    name = fields.Char(
        string="Reference",
        default="New",
        readonly=True,
        copy=False
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        tracking=True
    )

    manager_id = fields.Many2one(
        'hr.employee',
        string="Manager",
        related="employee_id.parent_id",
        store=True,
        readonly=True
    )

    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        related="employee_id.department_id",
        store=True
    )

    # request_by = fields.Many2one(
    #     'res.users',
    #     string="Requested By",
    #     default=lambda self: self.env.user,
    #     readonly=True
    # )

    request_by = fields.Many2one(
        'res.users',
        string="Requested By",
        readonly=True
    )

    # confirm_by = fields.Many2one(
    #     'res.users',
    #     string="Confirmed By",
    #     readonly=True
    # )

    approved_by = fields.Many2one(
        'res.users',
        string="Approved By",
        readonly=True
    )

    request_date = fields.Datetime(
        string="Request Date",
        default=fields.Datetime.now
    )

    confirm_date = fields.Datetime(
        string="Confirm Date",
        readonly=True
    )

    approved_date = fields.Datetime(
        string="Approved Date",
        readonly=True
    )

    project_id = fields.Many2one(
        'project.project',
        string="Project"
    )

    expense_account_id = fields.Many2one(
        'travel.expense.account',
        string="Expense Account"
    )

    # analytic_account_id = fields.Many2one(
    #     'account.analytic.account',
    #     string="Analytic Account"
    # )

    expense_ids = fields.One2many(
        'hr.expense',
        'travel_request_id',
        string="Generated Expenses"
    )

    # --------------------------
    # Travel Details
    # --------------------------

    travel_detail_line_ids = fields.One2many(
        'travel.detail.line',
        'travel_id',
        string="Travel Details"
    )

    first_travel_from = fields.Datetime(
        compute="_compute_first_travel_dates",
        store=False
    )

    first_travel_to = fields.Datetime(
        compute="_compute_first_travel_dates",
        store=False
    )

    accommodation_line_ids = fields.One2many(
        'travel.accommodation.line',
        'travel_id',
        string="Accommodation Details"
    )

    other_expense_line_ids = fields.One2many(
        'travel.other.expense.line',
        'travel_id',
        string="Other Expenses"
    )

    # travel_from = fields.Date(required=True)
    # travel_to = fields.Date(required=True)
    #
    # from_location = fields.Char(string="From Location")
    # to_location = fields.Char(string="To Location")

    # destination = fields.Char(required=True,string="Destination*")
    purpose = fields.Text()

    # contact_number = fields.Char()
    # email = fields.Char()

    # travel_mode = fields.Selection([
    #     ('flight', 'Flight'),
    #     ('train', 'Train'),
    #     ('car', 'Car'),
    #     ('bus', 'Bus')
    # ], string="Mode of Travel")
    #
    # days = fields.Integer(
    #     string="Days",
    #     compute="_compute_days",
    #     store=True
    # )

    # manager_comment = fields.Text(string="Manager Comment")

    # --------------------------
    # Other Info
    # --------------------------

    visible_to_user = fields.Boolean(
        compute="_compute_visible_to_user",
        store=True
    )

    available_departure_date = fields.Datetime(
        string="Available Departure Date"
    )

    available_return_date = fields.Datetime(
        string="Available Return Date"
    )

    departure_mode = fields.Selection([
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('car', 'Car'),
        ('bus', 'Bus')
    ], string="Departure Mode of Travel")

    return_mode = fields.Selection([
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('car', 'Car'),
        ('bus', 'Bus')
    ], string="Return Mode of Travel")

    visa_agent = fields.Many2one(
        'res.partner',
        string="Visa Agent"
    )

    ticket_booking_agent = fields.Many2one(
        'res.partner',
        string="Ticket Booking Agent"
    )

    description = fields.Html(string="Description")
    # attachment_ids = fields.Many2many(
    #     'ir.attachment',
    #     'travel_request_ir_attachments_rel',
    #     'travel_request_id',
    #     'attachment_id',
    #     string='Attachments'
    # )
    attachment_count = fields.Integer(
        string="Documents",
        compute="_compute_attachment_count"
    )

    paid_amount = fields.Monetary(
        string="Paid Amount",
        currency_field='currency_id'
    )

    is_paid = fields.Boolean(
        string="Is Paid"
    )

    # @api.depends('paid_amount')
    # def _compute_is_paid(self):
    #     for rec in self:
    #         rec.is_paid = rec.paid_amount > 0

    # travel_attachment_ids = fields.Many2many(
    #     'ir.attachment',
    #     'travel_request_travel_attachment_rel',  # relation table name
    #     'travel_request_id',
    #     'attachment_id',
    #     string="Travel Attachments",
    #     domain="[('res_model','=','travel.request'), ('travel_doc_type','=','travel')]"
    # )

    # accommodation_attachment_ids = fields.Many2many(
    #     'ir.attachment',
    #     'travel_request_accommodation_attachment_rel',  # different table
    #     'travel_request_id',
    #     'attachment_id',
    #     string="Accommodation Attachments",
    #     domain="[('res_model','=','travel.request'), ('travel_doc_type','=','accommodation')]"
    # )

    # travel_attachment_ids = fields.One2many(
    #     'ir.attachment',
    #     'res_id',
    #     domain=[('res_model', '=', 'travel.request'),
    #             ('travel_doc_type', '=', 'travel')],
    #     string="Travel Attachments"
    # )
    #
    # accommodation_attachment_ids = fields.One2many(
    #     'ir.attachment',
    #     'res_id',
    #     domain=[('res_model', '=', 'travel.request'),
    #             ('travel_doc_type', '=', 'accommodation')],
    #     string="Accommodation Attachments"
    # )
    def _compute_attachment_count(self):
        for rec in self:
            travel_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'travel.detail.line'),
                ('res_id', 'in', rec.travel_detail_line_ids.ids),
            ])

            accommodation_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'travel.accommodation.line'),
                ('res_id', 'in', rec.accommodation_line_ids.ids),
            ])

            other_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'travel.other.expense.line'),
                ('res_id', 'in', rec.other_expense_line_ids.ids),
            ])

            advance_extra_attachments = rec.advance_line_ids.mapped('extra_attachment_ids')

            all_attachments = (
                    travel_attachments |
                    accommodation_attachments |
                    other_attachments |
                    advance_extra_attachments
            )

            # all_attachments = (
            #         travel_attachments |
            #         accommodation_attachments |
            #         advance_extra_attachments
            # )

            rec.attachment_count = len(all_attachments)

    # def _compute_attachment_count(self):
    #     for rec in self:
    #         travel_ids = rec.travel_detail_line_ids.ids
    #         accommodation_ids = rec.accommodation_line_ids.ids
    #
    #         if not travel_ids and not accommodation_ids:
    #             rec.attachment_count = 0
    #             continue
    #
    #         domain = [
    #             ('res_model', 'in', ['travel.detail.line', 'travel.accommodation.line']),
    #             ('res_id', 'in', travel_ids + accommodation_ids)
    #         ]
    #
    #         rec.attachment_count = self.env['ir.attachment'].search_count(domain)

    # def _compute_attachment_count(self):
    #     for rec in self:
    #         travel_ids = rec.travel_detail_line_ids.ids
    #         accommodation_ids = rec.accommodation_line_ids.ids
    #
    #         attachments = self.env['ir.attachment'].search([
    #             '|',
    #             '&',
    #             ('res_model', '=', 'travel.detail.line'),
    #             ('res_id', 'in', travel_ids or [0]),
    #             '&',
    #             ('res_model', '=', 'travel.accommodation.line'),
    #             ('res_id', 'in', accommodation_ids or [0]),
    #         ])
    #
    #         rec.attachment_count = len(attachments)

    # def _compute_attachment_count(self):
    #     for rec in self:
    #         attachments = self.env['ir.attachment'].search([
    #             '|',
    #             '&',
    #             ('res_model', '=', 'travel.detail.line'),
    #             ('res_id', 'in', rec.travel_detail_line_ids.ids),
    #             '&',
    #             ('res_model', '=', 'travel.accommodation.line'),
    #             ('res_id', 'in', rec.accommodation_line_ids.ids),
    #         ])
    #
    #         rec.attachment_count = len(attachments)

    # def _compute_attachment_count(self):
    #     for rec in self:
    #         attachments = self.env['ir.attachment'].search([
    #             '|',
    #             ('res_model', '=', 'travel.detail.line'),
    #             ('res_model', '=', 'travel.accommodation.line'),
    #             ('res_id', 'in', rec.travel_detail_line_ids.ids + rec.accommodation_line_ids.ids)
    #         ])
    #         rec.attachment_count = len(attachments)

    # def _compute_attachment_count(self):
    #     for rec in self:
    #         rec.attachment_count = self.env['ir.attachment'].search_count([
    #             ('res_model', '=', 'travel.request'),
    #             ('res_id', '=', rec.id),
    #         ])

    # def _log_new_attachments(self):
    #     for rec in self:
    #
    #         attachments = self.env['ir.attachment'].search([
    #             ('res_model', 'in', [
    #                 'travel.detail.line',
    #                 'travel.accommodation.line',
    #                 'travel.other.expense.line'
    #             ]),
    #             ('res_id', 'in',
    #              rec.travel_detail_line_ids.ids +
    #              rec.accommodation_line_ids.ids +
    #              rec.other_expense_line_ids.ids
    #              )
    #         ])
    #
    #         existing_attachment_ids = rec.message_ids.mapped('attachment_ids').ids
    #
    #         new_attachments = attachments.filtered(
    #             lambda a: a.id not in existing_attachment_ids
    #         )
    #
    #         for att in new_attachments:
    #
    #             # 🔥 GET EXACT LINE
    #             line_info = ""
    #
    #             if att.res_model == 'travel.detail.line':
    #                 line = self.env['travel.detail.line'].browse(att.res_id)
    #                 line_info = f"From: {line.from_location} → {line.to_location}"
    #
    #             elif att.res_model == 'travel.accommodation.line':
    #                 line = self.env['travel.accommodation.line'].browse(att.res_id)
    #                 line_info = f"Hotel: {line.hotel_name} ({line.city})"
    #
    #             elif att.res_model == 'travel.other.expense.line':
    #                 line = self.env['travel.other.expense.line'].browse(att.res_id)
    #                 line_info = f"Expense: {line.expense_type_id.name}"
    #
    #             # ✅ COPY attachment
    #             new_attachment = att.copy({
    #                 'res_model': 'travel.request',
    #                 'res_id': rec.id,
    #             })
    #
    #             # ✅ POST ONLY THAT LINE INFO
    #             rec.message_post(
    #                 body=Markup(f"""
    #                     <b>📎 Attachment Added</b><br/>
    #                     {att.name}<br/>
    #                     <small>{line_info}</small>
    #                 """),
    #                 attachment_ids=[new_attachment.id],
    #                 subtype_xmlid="mail.mt_note"
    #             )

    # --------------------------
    # DEFAULTS
    # --------------------------
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        employee = self.env['hr.employee'].search([
            ('user_id', '=', self.env.user.id)
        ], limit=1)

        if employee:
            res['employee_id'] = employee.id

        return res

    def action_open_documents(self):
        self.ensure_one()

        # Travel line attachments
        travel_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'travel.detail.line'),
            ('res_id', 'in', self.travel_detail_line_ids.ids),
        ])

        # Accommodation attachments
        accommodation_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'travel.accommodation.line'),
            ('res_id', 'in', self.accommodation_line_ids.ids),
        ])

        other_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'travel.other.expense.line'),
            ('res_id', 'in', self.other_expense_line_ids.ids),
        ])

        # Advance line additional attachments
        advance_extra_attachments = self.advance_line_ids.mapped('extra_attachment_ids')

        # Combine all
        # all_attachments = (
        #         travel_attachments |
        #         accommodation_attachments |
        #         advance_extra_attachments
        # )

        all_attachments = (
                travel_attachments |
                accommodation_attachments |
                other_attachments |
                advance_extra_attachments
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', all_attachments.ids)],
        }

    def _compute_visible_to_user(self):
        user_employee = self.env.user.employee_id

        for rec in self:
            rec.visible_to_user = False

            emp = rec.employee_id

            # self
            if emp == user_employee:
                rec.visible_to_user = True
                continue

            # walk up hierarchy safely (NO child_of)
            while emp.parent_id:
                if emp.parent_id == user_employee:
                    rec.visible_to_user = True
                    break
                emp = emp.parent_id

    # def action_open_documents(self):
    #     self.ensure_one()
    #
    #     travel_line_ids = self.travel_detail_line_ids.ids
    #     accommodation_line_ids = self.accommodation_line_ids.ids
    #
    #     attachments = self.env['ir.attachment'].search([
    #         '|',
    #         '&',
    #         ('res_model', '=', 'travel.detail.line'),
    #         ('res_id', 'in', travel_line_ids),
    #         '&',
    #         ('res_model', '=', 'travel.accommodation.line'),
    #         ('res_id', 'in', accommodation_line_ids),
    #     ])
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Documents',
    #         'res_model': 'ir.attachment',
    #         'view_mode': 'list,form,kanban',
    #         'domain': [('id', 'in', attachments.ids)],
    #     }

    # def action_open_documents(self):
    #     self.ensure_one()
    #
    #     attachment_ids = (
    #             self.travel_attachment_ids.ids +
    #             self.accommodation_attachment_ids.ids
    #     )
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Documents',
    #         'res_model': 'ir.attachment',
    #         'view_mode': 'list,form,kanban',
    #         'domain': [('id', 'in', attachment_ids)],
    #     }
    # --------------------------
    # Accounting Info
    # --------------------------

    bank_name = fields.Many2one(
        'res.bank',
        string="Bank Name"
    )

    cheque_number = fields.Char(
        string="Cheque Number"
    )

    grand_total = fields.Monetary(
        string="Total Advance Amount",
        compute="_compute_grand_total",
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    @api.depends('advance_line_ids.status', 'advance_line_ids.subtotal')
    def _compute_grand_total(self):
        for rec in self:
            valid_lines = rec.advance_line_ids.filtered(lambda l: l.status != 'rejected')
            rec.grand_total = sum(valid_lines.mapped('subtotal'))
            # approved_lines = rec.advance_line_ids.filtered(lambda l: l.status == 'approved')
            # rec.grand_total = sum(approved_lines.mapped('subtotal'))
            # total = 0.0
            # for line in rec.advance_line_ids:
            #     if line.status == 'approved':
            #         total += line.subtotal
            # rec.grand_total = total

    # @api.depends('advance_line_ids.subtotal')
    # def _compute_grand_total(self):
    #     for rec in self:
    #         rec.grand_total = sum(rec.advance_line_ids.mapped('subtotal'))

    total_advance_amount = fields.Monetary(
        compute="_compute_total_advance",
        store=True,
        currency_field='company_currency_id'
    )

    company_currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    can_edit_paid = fields.Boolean(compute="_compute_can_edit_paid")

    def _compute_can_edit_paid(self):
        for rec in self:
            rec.can_edit_paid = rec.env.user.has_group(
                'employee_travel_requisition.group_travel_hr'
            )

    @api.depends('advance_line_ids.subtotal', 'advance_line_ids.status')
    def _compute_total_advance(self):
        for rec in self:
            valid_lines = rec.advance_line_ids.filtered(
                lambda l: l.status != 'rejected'
            )
            rec.total_advance_amount = sum(valid_lines.mapped('subtotal'))
            # approved_lines = rec.advance_line_ids.filtered(
            #     lambda l: l.status == 'approved'
            # )
            # rec.total_advance_amount = sum(approved_lines.mapped('subtotal'))

    # --------------------------
    # State
    # --------------------------
    # 23/3/2026
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('manager', 'Manager'),
        ('hr', 'HR/Accounts'),
        ('director', 'Director'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)

    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('submit', 'Submitted'),
    #     ('approved', 'Approved'),
    #     ('rejected', 'Rejected'),
    #     ('returned', 'Returned'),
    # ], default='draft', tracking=True)

    # --------------------------
    # Advance Payment Request
    # --------------------------

    advance_line_ids = fields.One2many(
        'travel.advance.line',
        'travel_id',
        string="Advance Payment Lines"
    )

    booking_agency = fields.Char(string="Booking Agency")

    status_id = fields.Many2one('travel.status', string="Status")
    purpose_of_visit_id = fields.Many2one('travel.purpose', string="Nature of Visit")
    # 25/3/2026
    manager_approved_by = fields.Many2one(
        'res.users', string="Manager Approved By", readonly=True
    )

    hr_approved_by = fields.Many2one(
        'res.users', string="HR Approved By", readonly=True
    )

    director_approved_by = fields.Many2one(
        'res.users', string="Director Approved By", readonly=True
    )

    # --------------------------
    # Sequence
    # --------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # 👇 YOUR EXISTING LOGIC
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'travel.request.seq'
                ) or 'New'

            if vals.get('employee_id'):
                employee = self.env['hr.employee'].browse(vals['employee_id'])
                if employee.user_id:
                    vals['request_by'] = employee.user_id.id

        records = super().create(vals_list)

        for rec in records:
            changes = []

            FIELDS_TO_SHOW = [
                'name',
                'employee_id',
                'manager_id',
                'department_id',
                'request_by',
                'request_date',
                'confirm_date',
                'approved_by',
                'approved_date',
                'purpose',
                'project_id',
                'expense_account_id',
                'state'
            ]

            for field in FIELDS_TO_SHOW:

                if field not in rec._fields:
                    continue

                value = rec[field]

                if not value:
                    continue

                field_obj = rec._fields[field]

                if hasattr(value, 'display_name'):
                    value = value.display_name

                changes.append(
                    f"<li><b>{field_obj.string}</b>: {value}</li>"
                )

            if changes:
                rec.sudo().message_post(
                    body=Markup(f"""
                        <b>🟢 Travel Request Created</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

        # 👇 TRACKING LOGIC
        # for rec, vals in zip(records, vals_list):
        #     changes = []

        # for field, value in vals.items():
        #     if field in rec._fields:
        #         field_label = rec._fields[field].string
        #
        #         if isinstance(rec[field], models.BaseModel):
        #             value = rec[field].display_name
        #
        #         if value in [False, None]:
        #             continue  # ✅ skip useless fields
        #
        #         changes.append(
        #             f"<li><b>{field_label}</b>: {value}</li>"
        #         )
        #
        # if changes:
        #     rec.message_post(
        #         body=Markup(f"""
        #         <b>🟢 Travel Request Created</b>
        #         <ul>
        #             {''.join(changes)}
        #         </ul>
        #         """),
        #         subtype_xmlid="mail.mt_note"
        #     )

        return records

    def write(self, vals):
        old_data = {}

        # ✅ store old values per record
        for rec in self:
            old_data[rec.id] = {
                field: rec[field]
                for field in vals
                if field in rec._fields
            }

        # ✅ your existing logic (KEEP)
        if vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            if employee.user_id:
                vals['request_by'] = employee.user_id.id

        result = super().write(vals)

        # ✅ tracking after write
        for rec in self:
            changes = []

            for field, old_val in old_data.get(rec.id, {}).items():

                field_obj = rec._fields[field]

                # ❌ SKIP one2many fields
                if field_obj.type == 'one2many':
                    continue

                new_val = rec[field]

                if old_val == new_val:
                    continue

                field_label = field_obj.string

                def format_value(value):
                    if hasattr(value, 'display_name'):
                        return value.display_name
                    if value in [False, None]:
                        return ""  # ✅ EMPTY
                    return value

                changes.append(
                    f"<li><b>{field_label}</b>: {format_value(old_val)} → {format_value(new_val)}</li>"
                )

            if changes:
                rec.sudo().message_post(
                    body=Markup(f"""
                    <b>✏️ Record Updated</b>
                    <ul>
                        {''.join(changes)}
                    </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

        for rec in self:
            is_paid = vals.get('is_paid', rec.is_paid)
            paid_amount = vals.get('paid_amount', rec.paid_amount)

            if is_paid and paid_amount > 0 and rec.state != 'paid':
                super(TravelRequest, rec).write({'state': 'paid'})

        # # ✅ AFTER EVERYTHING
        # self._log_new_attachments()

        return result

    @api.depends('expense_ids.total_amount_currency')
    def _compute_paid_amount(self):
        for rec in self:
            rec.paid_amount = sum(rec.expense_ids.mapped('total_amount_currency'))

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and self.employee_id.user_id:
            self.request_by = self.employee_id.user_id

    @api.depends('travel_detail_line_ids.travel_from',
                 'travel_detail_line_ids.travel_to')
    def _compute_first_travel_dates(self):
        for rec in self:
            if rec.travel_detail_line_ids:
                rec.first_travel_from = rec.travel_detail_line_ids[0].travel_from
                rec.first_travel_to = rec.travel_detail_line_ids[0].travel_to
            else:
                rec.first_travel_from = False
                rec.first_travel_to = False

    # --------------------------
    # Validations
    # --------------------------

    # @api.constrains('travel_from', 'travel_to')
    # def _check_dates(self):
    #     for rec in self:
    #         if rec.travel_to and rec.travel_from:
    #             if rec.travel_to < rec.travel_from:
    #                 raise ValidationError(
    #                     "Travel End Date cannot be before Start Date."
    #                 )

    # --------------------------
    # Buttons
    # --------------------------
    # 23/3/2026
    def action_submit(self):
        for rec in self:

            if rec.state != 'draft':
                raise ValidationError("Only Draft can be submitted.")

            # if not rec.travel_detail_line_ids:
            #     raise ValidationError("Add Travel Details.")

            if not rec.advance_line_ids:
                raise ValidationError("Add Advance Payment lines.")

            rec.state = 'manager'

            _logger.error("MANAGER: %s", rec.manager_id)
            _logger.error("USER: %s", rec.manager_id.user_id)
            _logger.error("EMAIL: %s", rec.manager_id.user_id.email if rec.manager_id.user_id else None)

            if rec.manager_id and rec.manager_id.user_id and rec.manager_id.user_id.email:
                rec._send_mail(
                    'employee_travel_requisition.email_travel_submit',
                    rec.manager_id.user_id.email
                )
            rec.confirm_date = fields.Datetime.now()

        # for rec in self:
        #     _logger.warning("STATE BEFORE: %s", rec.state)
        #
        #     rec.state = 'manager'
        #
        #     _logger.warning("STATE AFTER: %s", rec.state)

    # def action_to_manager(self):
    #     for rec in self:
    #
    #         if rec.state != 'submitted':
    #             raise ValidationError("Only Submitted records allowed.")
    #
    #         rec.state = 'manager'

    # def action_move_to_hr(self):
    #     for rec in self:
    #
    #         if rec.state != 'manager':
    #             raise ValidationError("Not in Manager stage.")
    #
    #         # ✅ ALL LINES MUST BE PROCESSED
    #         pending = rec.advance_line_ids.filtered(lambda l: l.status == 'draft')
    #
    #         if pending:
    #             raise ValidationError("All lines must be approved/rejected by Manager.")
    #
    #         rec.state = 'hr'
    #
    #         if rec.travel_id:
    #             travel = rec.travel_id
    #
    #             pending = travel.advance_line_ids.filtered(lambda l: l.status == 'draft')
    #
    #             if not pending:
    #                 travel.state = 'hr'

    def action_hr_approve(self):
        for rec in self:

            if rec.state != 'hr':
                raise ValidationError("Not in HR stage.")

            # ✅ Must have at least one approved line
            approved_lines = rec.advance_line_ids.filtered(lambda l: l.status == 'approved')

            if not approved_lines:
                raise ValidationError("No approved lines.")

            # rec.director_approved_by = self.env.user
            rec.hr_approved_by = self.env.user
            rec.state = 'director'

            director = rec.manager_id.parent_id and rec.manager_id.parent_id.parent_id

            if director and director.user_id and director.user_id.email:
                rec._send_mail(
                    'employee_travel_requisition.email_hr_to_director',
                    director.user_id.email
                )

    def action_hr_reject(self):
        for rec in self:
            rec.state = 'rejected'

            if rec.employee_id and rec.employee_id.user_id and rec.employee_id.user_id.email:
                rec._send_mail(
                    'employee_travel_requisition.email_travel_rejected',
                    rec.employee_id.user_id.email
                )

    def action_director_approve(self):
        for rec in self:

            if rec.state != 'director':
                raise ValidationError("Not in Director stage.")

            if rec.expense_ids:
                raise ValidationError("Expenses already generated.")

            # ✅ Get approved lines
            approved_lines = rec.advance_line_ids.filtered(
                lambda l: l.status == 'approved'
            )

            if not approved_lines:
                raise ValidationError("No approved lines.")

            total_amount = sum(
                line.unit_price * line.quantity
                for line in approved_lines
            )

            # total_amount = sum(approved_lines.mapped('subtotal'))

            # if total_amount <= 0:
            #     raise ValidationError("Total amount must be greater than 0.")

            # ✅ Get product
            product = self.env['product.product'].search(
                [('default_code', '=', 'TRANS & ACC')],
                limit=1
            )

            if not product:
                raise ValidationError("TRANS & ACC product not found.")

            # ✅ CREATE EXPENSE HERE (ONLY HERE)
            expense = self.env['hr.expense'].sudo().create({
                'name': f"{rec.name} - Travel & Accommodation",
                'employee_id': rec.employee_id.id,
                'product_id': product.id,
                'date': fields.Date.today(),
                'quantity': 1,
                'total_amount_currency': total_amount,
                'travel_request_id': rec.id,
            })

            # ✅ ADD FOLLOWERS (IMPORTANT)
            partners = []

            if rec.employee_id.user_id:
                partners.append(rec.employee_id.user_id.partner_id.id)

            if rec.manager_id and rec.manager_id.user_id:
                partners.append(rec.manager_id.user_id.partner_id.id)

            if partners:
                expense.message_subscribe(partner_ids=partners)

            # ✅ Link other expense lines
            for other in rec.other_expense_line_ids:
                other.sudo().write({
                    'expense_id': expense.id
                })

            rec.director_approved_by = self.env.user
            rec.approved_by = self.env.user
            rec.approved_date = fields.Datetime.now()
            rec.state = 'approved'
            if rec.employee_id and rec.employee_id.user_id and rec.employee_id.user_id.email:
                rec._send_mail(
                    'employee_travel_requisition.email_director_to_user',
                    rec.employee_id.user_id.email
                )

    def _send_mail(self, template_xmlid, email_to):
        template = self.env.ref(template_xmlid, raise_if_not_found=False)

        if not template or not email_to:
            return

        for rec in self:

            mail_id = template.sudo().send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_to': email_to,
                }
            )

            mail = self.env['mail.mail'].sudo().browse(mail_id)
            if mail:
                mail.sudo().write({
                    'auto_delete': False  # 🔥 force persist
                })
                # mail.sudo().send()

            rec.message_post(
                body=f"📧 Email sent to {email_to}",
                subtype_xmlid="mail.mt_note"
            )

            # 🔥 ALSO POST ON EXPENSE
            if rec.expense_ids:
                expense = rec.expense_ids[0]

                expense.message_post(
                    body=f"📧 Email sent to {email_to}",
                    subtype_xmlid="mail.mt_note"
                )

    # def _send_mail(self, template_xmlid, email_to):
    #     template = self.env.ref(template_xmlid, raise_if_not_found=False)
    #
    #     if not template or not email_to:
    #         return
    #
    #     for rec in self:
    #         template.send_mail(
    #             rec.id,
    #             force_send=True,
    #             email_values={'email_to': email_to}
    #         )

    # # ✅ THIS IS THE KEY FIX
    # rec.message_post_with_template(template.id)

    # def _send_mail(self, template_xmlid, email_to):
    #     template = self.env.ref(template_xmlid, raise_if_not_found=False)
    #
    #     if not template:
    #         _logger.error("❌ TEMPLATE NOT FOUND: %s", template_xmlid)
    #         return
    #
    #     if not email_to:
    #         _logger.error("❌ EMAIL NOT FOUND for record %s", self.ids)
    #         return
    #
    #     for rec in self:
    #         _logger.error("📧 SENDING EMAIL TO: %s", email_to)
    #
    #         template.send_mail(
    #             rec.id,
    #             force_send=True,
    #             email_values={'email_to': email_to}
    #         )
    #
    #         # ✅ SAFE CHATTER LOG
    #         rec.message_post(
    #             body=f"📧 Email sent to {email_to}",
    #             subtype_xmlid="mail.mt_note"
    #         )

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'

            if rec.employee_id and rec.employee_id.user_id and rec.employee_id.user_id.email:
                rec._send_mail(
                    'employee_travel_requisition.email_travel_rejected',
                    rec.employee_id.user_id.email
                )

            # def action_submit(self):
            #     for rec in self:
            #         # if not rec.to_location:
            #         if not rec.travel_detail_line_ids:
            #             raise ValidationError("To Location is required.")
            #         rec.state = 'submit'
            #         # rec.confirm_by = self.env.user
            #         rec.confirm_date = fields.Date.today()

            # def action_submit(self):
            #     for rec in self:
            #         if not rec.destination:
            #             raise ValidationError("Destination is required.")
            #         rec.state = 'submit'
            #         rec.confirm_by = self.env.user
            #         rec.confirm_date = fields.Date.today()

            # def action_approve(self):
            #     self.state = 'approved'
            #     self.approved_by = self.env.user
            #     self.approved_date = fields.Date.today()

            # def action_approve(self):
            #     for rec in self:
            #
            #         if rec.expense_ids:
            #             raise ValidationError("Expenses already generated.")
            #
            #         rec.state = 'approved'
            #         rec.approved_by = self.env.user
            #         rec.approved_date = fields.Date.today()
            #
            #         product = self.env['product.product'].search(
            #             [('default_code', '=', 'TRANS & ACC')],
            #             limit=1
            #         )
            #
            #         if not product:
            #             raise ValidationError("TRANS & ACC product not found.")
            #
            #         # Sync expense manager
            #         if rec.manager_id and rec.manager_id.user_id:
            #             rec.employee_id.expense_manager_id = rec.manager_id.user_id
            #
            #         # # ==============================
            #         # # TRAVEL LINES
            #         # # ==============================
            #         # for travel in rec.travel_detail_line_ids:
            #         #     description = (
            #         #         f"From: {travel.from_location or ''} | "
            #         #         f"To: {travel.to_location or ''} | "
            #         #         f"Departure: {travel.travel_from or ''} | "
            #         #         f"Return: {travel.travel_to or ''} | "
            #         #         f"Mode: {travel.travel_mode or ''} | "
            #         #         f"Days: {travel.days or 0}"
            #         #     )
            #         #
            #         #     self.env['travel.advance.line'].create({
            #         #         'travel_id': rec.id,
            #         #         'expense_id': product.id,
            #         #         'description': description,
            #         #         'unit_price': 0.0,
            #         #         'quantity': 1,
            #         #         'type': 'travel',
            #         #     })
            #         #
            #         # # ==============================
            #         # # ACCOMMODATION LINES
            #         # # ==============================
            #         # for accom in rec.accommodation_line_ids:
            #         #     description = (
            #         #         f"Hotel: {accom.hotel_name or ''} | "
            #         #         f"City: {accom.city or ''} | "
            #         #         f"Check-In: {accom.check_in_date or ''} | "
            #         #         f"Check-Out: {accom.check_out_date or ''} | "
            #         #         f"Ref: {accom.booking_reference or ''}"
            #         #     )
            #         #
            #         #     self.env['travel.advance.line'].create({
            #         #         'travel_id': rec.id,
            #         #         'expense_id': product.id,
            #         #         'description': description,
            #         #         'unit_price': 0.0,
            #         #         'quantity': 1,
            #         #         'type': 'accommodation',
            #         #     })
            #
            #         # ==============================
            #         # CREATE HR EXPENSES
            #         # ==============================
            #
            #         approved_lines = rec.advance_line_ids.filtered(
            #             lambda l: l.status == 'approved'
            #         )
            #
            #         total_amount = sum(approved_lines.mapped('subtotal'))
            #
            #         if total_amount <= 0:
            #             raise ValidationError("No approved lines to generate expense.")
            #
            #         expense = self.env['hr.expense'].create({
            #             'name': f"{rec.name} - Travel & Accommodation",
            #             'employee_id': rec.employee_id.id,
            #             'product_id': product.id,
            #             'date': fields.Date.today(),
            #             'quantity': 1,
            #             'total_amount_currency': total_amount,
            #             'travel_request_id': rec.id,
            #         })

            # ==============================
            # COPY OTHER EXPENSE LINES
            # ==============================

            # for other in rec.other_expense_line_ids:
            #     other.with_context(skip_attachment_log=True).write({
            #         'expense_id': expense.id
            #     })
            # other.expense_id = expense.id

            # for other in rec.other_expense_line_ids:
            #     self.env['travel.other.expense.line'].create({
            #         'travel_id': rec.id,
            #         'expense_id': expense.id,
            #         'expense_type_id': other.expense_type_id.id,
            #         'description': other.description,
            #         'expense_date': other.expense_date,
            #     })

            # self.env['hr.expense'].create({
            #     'name': f"{rec.name} - Travel & Accommodation",
            #     'employee_id': rec.employee_id.id,
            #     'product_id': product.id,
            #     'date': fields.Date.today(),
            #     'quantity': 1,
            #     'total_amount_currency': total_amount,
            #     'travel_request_id': rec.id,
            # })
            # total_amount = sum(rec.advance_line_ids.mapped('subtotal'))
            #
            # if total_amount > 0:
            #     self.env['hr.expense'].create({
            #         'name': f"{rec.name} - Travel & Accommodation",
            #         'employee_id': rec.employee_id.id,
            #         'product_id': product.id,
            #         'date': fields.Date.today(),
            #         'total_amount_currency': total_amount,
            #         'quantity': 1,
            #         'travel_request_id': rec.id,
            #     })

            # for line in rec.advance_line_ids:
            #     self.env['hr.expense'].create({
            #         'name': f"{rec.name} - {line.description}",
            #         'employee_id': rec.employee_id.id,
            #         'product_id': product.id,
            #         'date': fields.Date.today(),
            #         'quantity': 1,
            #         'total_amount_currency': line.subtotal,
            #         'travel_request_id': rec.id,
            #     })

    # def action_approve(self):
    #     for rec in self:
    #
    #         if rec.expense_ids:
    #             raise ValidationError("Expenses already generated.")
    #
    #         rec.state = 'approved'
    #         rec.approved_by = self.env.user
    #         rec.approved_date = fields.Date.today()
    #
    #         # --------------------------
    #         # CLEAR OLD ADVANCE LINES
    #         # --------------------------
    #         rec.advance_line_ids.unlink()
    #
    #         # --------------------------
    #         # GENERATE FROM TRAVEL DETAILS
    #         # --------------------------
    #         for line in rec.travel_detail_line_ids:
    #             description = f"{line.from_location} → {line.to_location} ({line.travel_from} to {line.travel_to})"
    #
    #             self.env['travel.advance.line'].create({
    #                 'travel_id': rec.id,
    #                 'type': 'travel',
    #                 'description': description,
    #                 'unit_price': 0.0,
    #                 'quantity': 1,
    #             })
    #
    #         # --------------------------
    #         # GENERATE FROM ACCOMMODATION
    #         # --------------------------
    #         for line in rec.accommodation_line_ids:
    #             description = f"{line.hotel_name} - {line.city} ({line.check_in_date} to {line.check_out_date})"
    #
    #             self.env['travel.advance.line'].create({
    #                 'travel_id': rec.id,
    #                 'type': 'accommodation',
    #                 'description': description,
    #                 'unit_price': 0.0,
    #                 'quantity': 1,
    #             })
    #
    #         product = self.env['product.product'].search(
    #             [('default_code', '=', 'TRANS & ACC')],
    #             limit=1
    #         )
    #
    #         if not product:
    #             raise ValidationError("TRANS & ACC product not found.")
    #
    #         # Sync employee expense manager
    #         if rec.manager_id and rec.manager_id.user_id:
    #             rec.employee_id.expense_manager_id = rec.manager_id.user_id
    #
    #
    #
    #         for line in rec.advance_line_ids:
    #
    #             # Sync employee expense manager with travel manager
    #             if rec.manager_id and rec.manager_id.user_id:
    #                 rec.employee_id.expense_manager_id = rec.manager_id.user_id
    #
    #
    #             expense_vals = {
    #                 'name': f"{rec.name} - {line.description or product.name}",
    #                 'employee_id': rec.employee_id.id,
    #                 'product_id': product.id,
    #                 # 'date': rec.travel_from,
    #                 'date': rec.travel_detail_line_ids and rec.travel_detail_line_ids[
    #                     0].travel_from or fields.Date.today(),
    #                 'quantity': 1,
    #                 'total_amount_currency': line.subtotal,
    #                 'travel_request_id': rec.id,
    #             }
    #
    #             self.env['hr.expense'].create(expense_vals)

    # for line in rec.advance_line_ids:
    #     self.env['hr.expense'].create({
    #         'name': f"{rec.name} - {line.description or product.name}",
    #         'employee_id': rec.employee_id.id,
    #         'product_id': product.id,
    #         'unit_amount': line.unit_price,
    #         'quantity': line.quantity,
    #         'date': rec.travel_from,
    #         'travel_request_id': rec.id,
    #     })
    # self.env['hr.expense'].create({
    #     'name': f"{rec.name} - {line.description or product.name}",
    #     'employee_id': rec.employee_id.id,
    #     'product_id': product.id,
    #     'unit_amount': line.unit_price,
    #     'quantity': line.quantity,
    #     'date': rec.travel_from,
    #     'travel_request_id': rec.id,
    # })

    # def action_reject(self):
    #     self.state = 'rejected'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

            # ✅ reset line statuses
            rec.advance_line_ids.write({'status': 'draft'})

            rec.manager_approved_by = False
            rec.hr_approved_by = False
            rec.director_approved_by = False
            rec.approved_by = False
            rec.approved_date = False

    # def action_reset_draft(self):
    #     self.state = 'draft'


class TravelAdvanceLine(models.Model):
    _name = 'travel.advance.line'
    _description = 'Travel Advance Payment Line'

    # ✅ Define default method FIRST
    def _default_expense_product(self):
        return self.env['product.product'].search(
            [('default_code', '=', 'TRANS & ACC')],
            limit=1
        )

    travel_id = fields.Many2one(
        'travel.request',
        string="Travel Request",
        ondelete='cascade'
    )

    expense_id = fields.Many2one(
        'product.product',
        string="Expense",
        default=_default_expense_product,
        required=True
    )

    description = fields.Char(string="Details")
    line_description = fields.Char(string="Description")
    booking_agency = fields.Char(string="Booking Agency")

    unit_price = fields.Float(string="Actual Price")

    quantity = fields.Float(
        string="Quantity",
        default=1
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )

    subtotal = fields.Monetary(
        compute="_compute_subtotal",
        store=True,
        currency_field='currency_id'
    )

    status = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', string="Budget Status")

    account_remarks = fields.Text(string="Accounts Remarks")

    line_type = fields.Selection([
        ('travel', 'Travel'),
        ('accommodation', 'Accommodation'),
        ('other', 'Other')
    ], string="Type", required=True)

    travel_detail_line_id = fields.Many2one(
        'travel.detail.line',
        string="Travel Detail Line"
    )

    accommodation_line_id = fields.Many2one(
        'travel.accommodation.line',
        string="Accommodation Line"
    )

    other_expense_line_id = fields.Many2one(
        'travel.other.expense.line',
        string="Other Expense Line"
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string="Attachments",
        compute="_compute_attachments",
        store=True,
        # readonly=True
    )

    extra_attachment_ids = fields.Many2many(
        'ir.attachment',
        'travel_advance_extra_attachment_rel',
        'advance_line_id',
        'attachment_id',
        string="Additional Attachments"
    )

    review_status = fields.Selection([
        ('pending', 'Pending'),
        ('checked', 'Checked'),
        ('on_hold', 'On Hold'),
    ], default='pending', string="Review Status")

    can_review = fields.Boolean(
        compute="_compute_can_review",
        store=False
    )

    approved_subtotal = fields.Monetary(
        string="Approved Budget",
        currency_field='currency_id',
        readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            # ✅ FIX: detect hr.expense creation reliably
            if self.env.context.get('from_hr_expense') or vals.get('travel_id'):

                vals['status'] = 'approved'

                # optional (good practice)
                if vals.get('unit_price') and vals.get('quantity'):
                    vals['approved_subtotal'] = vals['unit_price'] * vals['quantity']

        return super().create(vals_list)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if self.env.context.get('from_hr_expense'):
    #             vals['status'] = 'approved'
    #     return super().create(vals_list)

    def write(self, vals):

        # ✅ force approved when editing from hr.expense
        if self.env.context.get('from_hr_expense'):
            vals['status'] = 'approved'

        # 🛑 STOP RECURSION
        if self.env.context.get('skip_sync'):
            return super(TravelAdvanceLine, self).write(vals)

        res = super().write(vals)

        if 'review_status' in vals:
            for rec in self:
                if rec.review_status == 'checked':
                    travel = rec.travel_id

                    if not travel:
                        continue

                    expense = travel.expense_ids and travel.expense_ids[0] or False

                    if not expense:
                        continue

                    # count
                    total = len(travel.advance_line_ids)
                    checked = len(travel.advance_line_ids.filtered(lambda l: l.review_status == 'checked'))

                    body = f"""
                    <p><b>Advance Review Update</b></p>
                    <p>Checked: <b>{checked}/{total}</b></p>
                    <p>Line: <b>{rec.description or ''}</b></p>
                    """

                    # ✅ SEND EMAIL
                    template = self.env.ref(
                        'employee_travel_requisition.email_line_checked',
                        raise_if_not_found=False
                    )

                    if template and travel.employee_id.user_id.email:
                        template.sudo().send_mail(
                            expense.id,
                            force_send=True,
                            email_values={
                                'email_to': travel.employee_id.user_id.email
                            }
                        )

                    # ✅ CHATTER IN EXPENSE
                    expense.message_post(
                        body=Markup(body),
                        partner_ids=[travel.employee_id.user_id.partner_id.id]
                    )

        # -----------------------------------
        # 🔥 ADD THIS BLOCK (SYNC BACK)
        # -----------------------------------

        # 🚫 BLOCK BACK SYNC IF LINKED TO EXPENSE
        if any(rec.travel_id and rec.travel_id.expense_ids for rec in self):
            return res

        for rec in self:

            update_vals = {}

            if 'unit_price' in vals:
                update_vals['unit_price'] = rec.unit_price

            if 'line_description' in vals or 'description' in vals:
                update_vals['description'] = rec.line_description or rec.description

            if not update_vals:
                continue

            # ✅ TRAVEL
            if rec.travel_detail_line_id:
                rec.travel_detail_line_id.with_context(skip_sync=True).write(update_vals)

            # ✅ ACCOMMODATION
            elif rec.accommodation_line_id:
                rec.accommodation_line_id.with_context(skip_sync=True).write(update_vals)

            # ✅ OTHER EXPENSE
            elif rec.other_expense_line_id:
                rec.other_expense_line_id.with_context(skip_sync=True).write(update_vals)

        # -----------------------------------
        # ✅ RETURN LAST
        # -----------------------------------

        return res

    def _send_review_status_email(self):
        for rec in self:
            travel = rec.travel_id
            if not travel:
                continue

            expense = travel.expense_ids and travel.expense_ids[0] or False

            total = len(travel.advance_line_ids)
            checked = len(travel.advance_line_ids.filtered(lambda l: l.review_status == 'checked'))
            on_hold = len(travel.advance_line_ids.filtered(lambda l: l.review_status == 'on_hold'))

            body = f"""
            <p><b>Advance Review Update</b></p>

            <p>
            Checked: <b>{checked}/{total}</b><br/>
            On Hold: <b>{on_hold}</b>
            </p>

            <p>
            Latest Updated Line: <b>{rec.description or ''}</b>
            </p>
            """

            template = self.env.ref(
                'employee_travel_requisition.email_line_checked',
                raise_if_not_found=False
            )

            # ✅ EMAIL + CHATTER ON EXPENSE
            if expense and template and travel.employee_id.user_id:
                template.send_mail(
                    travel.id,
                    force_send=True,
                    email_values={
                        'email_to': travel.employee_id.user_id.email
                    }
                )

                expense.message_post(
                    body=Markup(body),
                    partner_ids=[travel.employee_id.user_id.partner_id.id]
                )

    def action_open_attachments(self):
        self.ensure_one()

        if not self.attachment_ids:
            return

        attachment = self.attachment_ids[0]

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=false',
            'target': 'self',
        }

    @api.depends('unit_price', 'quantity', 'status', 'approved_subtotal')
    def _compute_subtotal(self):
        for line in self:
            # 🔒 Freeze ONLY after approval
            if line.status == 'approved' and line.approved_subtotal:
                line.subtotal = line.approved_subtotal
            else:
                # ✅ KEEP ORIGINAL LOGIC (DO NOT TOUCH)
                line.subtotal = line.unit_price * line.quantity

    def action_approve_line(self):
        for rec in self:

            # ✅ ADD THIS LINE (FREEZE BUDGET)
            rec.approved_subtotal = rec.unit_price * rec.quantity

            rec.status = 'approved'

            if rec.travel_id:
                travel = rec.travel_id

                # ✅ CHECK IF ALL LINES PROCESSED
                pending = travel.advance_line_ids.filtered(lambda l: l.status == 'draft')

                if not pending and travel.state == 'manager':
                    travel.manager_approved_by = self.env.user
                    travel.state = 'hr'

                    # send to HR (manager's manager)
                    hr = travel.manager_id.parent_id

                    if hr and hr.user_id and hr.user_id.email:
                        travel._send_mail(
                            'employee_travel_requisition.email_manager_to_hr',
                            hr.user_id.email
                        )

                travel.sudo().message_post(
                    body=Markup(f"""
                        <b>✅ Advance Line Approved</b><br/>
                        <small>{rec.description or ''}</small>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

    def action_reject_line(self):
        for rec in self:
            rec.status = 'rejected'

            if rec.travel_id:
                travel = rec.travel_id

                pending = travel.advance_line_ids.filtered(lambda l: l.status == 'draft')

                if not pending and travel.state == 'manager':
                    travel.manager_approved_by = self.env.user
                    travel.state = 'hr'

                    hr = travel.manager_id.parent_id

                    if hr and hr.user_id and hr.user_id.email:
                        travel._send_mail(
                            'employee_travel_requisition.email_manager_to_hr',
                            hr.user_id.email
                        )

                travel.sudo().message_post(
                    body=Markup(f"""
                        <b>❌ Advance Line Rejected</b><br/>
                        <small>{rec.description or ''}</small>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

    def action_mark_checked(self):
        for rec in self:
            rec.review_status = 'checked'
            rec._send_review_status_email()

    def action_mark_on_hold(self):
        for rec in self:
            rec.review_status = 'on_hold'
            rec._send_review_status_email()

    @api.depends(
        'travel_detail_line_id',
        'travel_detail_line_id.attachment_ids',
        'accommodation_line_id',
        'accommodation_line_id.attachment_ids',
        'other_expense_line_id',
        'other_expense_line_id.attachment_ids'
    )
    def _compute_attachments(self):
        for rec in self:
            if rec.travel_detail_line_id:
                rec.attachment_ids = rec.travel_detail_line_id.attachment_ids
            elif rec.accommodation_line_id:
                rec.attachment_ids = rec.accommodation_line_id.attachment_ids
            elif rec.other_expense_line_id:
                rec.attachment_ids = rec.other_expense_line_id.attachment_ids
            else:
                rec.attachment_ids = [(5, 0, 0)]

    def _compute_can_review(self):
        for rec in self:
            rec.can_review = False

            if rec.travel_id and rec.travel_id.expense_ids:
                expense = rec.travel_id.expense_ids[0]

                # Allow review only when expense is submitted
                if expense.state == 'submit':
                    rec.can_review = True


class TravelDetailLine(models.Model):
    _name = 'travel.detail.line'
    _description = 'Travel Detail Line'
    _inherit = ['travel.sync.mixin', 'attachment.chatter.mixin']

    unit_price = fields.Float(string="Unit Price")

    travel_id = fields.Many2one(
        'travel.request',
        ondelete='cascade'
    )

    from_location = fields.Char(string="From")
    to_location = fields.Char(string="To")
    travel_from = fields.Datetime(string="Departure Date")
    travel_to = fields.Datetime(string="Return Date")
    travel_mode_id = fields.Many2one(
        'travel.mode',
        string="Mode of Travel"
    )
    booking_agency = fields.Char(string="Booking Agency")
    account_remarks = fields.Text(string="Accounts Remarks")

    contact_number = fields.Char()
    email = fields.Char()

    description = fields.Char(string="Description")

    days = fields.Integer(
        compute="_compute_days",
        store=True
    )

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string="Attachments",
        domain=[('res_model', '=', 'travel.detail.line')]
    )

    def _post_attachments_to_chatter(self):
        self._post_line_attachments_to_chatter(
            'travel.detail.line',
            lambda r: f"From: {r.from_location} → {r.to_location}"
        )

    @api.depends('travel_from', 'travel_to')
    def _compute_days(self):
        for rec in self:
            if rec.travel_from and rec.travel_to:
                rec.days = (rec.travel_to - rec.travel_from).days
            else:
                rec.days = 0

    def write(self, vals):
        if self.env.context.get('skip_sync'):
            return super(TravelDetailLine, self).write(vals)

        old_data = {}

        for rec in self:
            old_data[rec.id] = {
                field: rec[field]
                for field in vals
                if field in rec._fields
            }

        result = super().write(vals)

        self._sync_to_advance(vals, 'travel_detail_line_id')

        for rec in self:
            changes = []

            for field, old_val in old_data.get(rec.id, {}).items():
                new_val = rec[field]

                if old_val == new_val:
                    continue

                field_label = rec._fields[field].string

                def format_value(value):
                    if hasattr(value, 'display_name'):
                        return value.display_name
                    return value if value not in [False, None] else "—"

                changes.append(
                    f"<li><b>{field_label}</b>: {format_value(old_val)} → {format_value(new_val)}</li>"
                )

            if changes and rec.travel_id:
                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>✏️ Travel Detail Updated</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

        for rec in self:
            if not self.env.context.get('skip_attachment_log'):
                rec._post_attachments_to_chatter()

        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        product = self.env['product.product'].search(
            [('default_code', '=', 'TRANS & ACC')],
            limit=1
        )

        if not product:
            raise ValidationError("TRANS & ACC product not found.")

        for record in records:
            description = (
                f"From: {record.from_location or ''} | "
                f"To: {record.to_location or ''} | "
                f"Departure: {record.travel_from or ''} | "
                f"Return: {record.travel_to or ''} | "
                f"Mode: {record.travel_mode_id.name or ''}"
            )

            self.env['travel.advance.line'].create({
                'travel_id': record.travel_id.id,
                'travel_detail_line_id': record.id,
                'expense_id': product.id,
                'description': description,
                'line_description': record.description,
                'unit_price': record.unit_price,
                'line_type': 'travel',
            })

        for rec in records:
            if not rec.travel_id:
                continue

            changes = []

            def format_value(value):
                if hasattr(value, 'display_name'):
                    return value.display_name
                return value if value not in [False, None] else "—"

            EXCLUDE_FIELDS = [
                'id',
                'create_uid', 'create_date',
                'write_uid', 'write_date',
                'display_name', '__last_update'
            ]

            for field, field_obj in rec._fields.items():

                # ❌ skip junk
                if field in EXCLUDE_FIELDS:
                    continue

                # ❌ skip relational noise
                if field_obj.type in ['one2many', 'many2many']:
                    continue

                value = rec[field]

                if not value:
                    continue

                value = format_value(value)

                changes.append(
                    f"<li><b>{field_obj.string}</b>: {value}</li>"
                )

            # fields_to_track = [
            #     field for field in rec._fields
            #     if rec._fields[field].type not in ['one2many', 'many2many']
            # ]
            #
            # for field in fields_to_track:
            #     if field in rec._fields:
            #         value = rec[field]
            #         if value:
            #             changes.append(
            #                 f"<li><b>{rec._fields[field].string}</b>: {format_value(value)}</li>"
            #             )

            if changes:
                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>➕ Travel Detail Added</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

        for rec in records:
            if not self.env.context.get('skip_attachment_log'):
                rec._post_attachments_to_chatter()
            # rec._post_attachments_to_chatter()

            # for rec in records:
            #     rec._post_attachments_to_chatter()

        return records


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    total_budget = fields.Monetary(
        string="Total Budget",
        related="travel_request_id.total_advance_amount",
        currency_field='currency_id',
        store=True,
        readonly=True
    )

    paid_amount = fields.Monetary(
        string="Paid Amount",
        related="travel_request_id.paid_amount",
        currency_field='currency_id',
        store=True,
        readonly=True
    )

    travel_request_id = fields.Many2one(
        'travel.request',
        string="Travel Request"
    )

    travel_detail_line_ids = fields.One2many(
        related='travel_request_id.travel_detail_line_ids',
        readonly=True
    )

    accommodation_line_ids = fields.One2many(
        related='travel_request_id.accommodation_line_ids',
        string="Accommodation Details",
        readonly=True
    )

    advance_line_ids = fields.One2many(
        'travel.advance.line',
        related='travel_request_id.advance_line_ids',
        string="Advance Payment Request",
        readonly=False,
        context={'from_hr_expense': True},
        # domain=[('status', '=', 'approved')]
    )

    approved_advance_line_ids = fields.One2many(
        'travel.advance.line',
        compute='_compute_approved_advance_lines',
        inverse='_inverse_approved_advance_lines',
        string="Advance Payment Request"
    )

    # advance_line_ids = fields.One2many(
    #     related='travel_request_id.advance_line_ids',
    #     string="Advance Payment Request",
    #     readonly=False
    # )

    # travel_from = fields.Date(related='travel_request_id.travel_from', store=False)
    # travel_to = fields.Date(related='travel_request_id.travel_to', store=False)
    # from_location = fields.Char(related='travel_request_id.from_location')
    # to_location = fields.Char(related='travel_request_id.to_location')
    # travel_mode = fields.Selection(related='travel_request_id.travel_mode')

    purpose = fields.Text(
        related='travel_request_id.purpose',
        readonly=True
    )

    project_id = fields.Many2one(
        'project.project',
        related='travel_request_id.project_id',
        readonly=True
    )

    expense_account_id = fields.Many2one(
        'travel.expense.account',
        related='travel_request_id.expense_account_id',
        readonly=True,
        store=True
    )

    attachment_count = fields.Integer(
        compute="_compute_attachment_count"
    )

    other_expense_line_ids = fields.One2many(
        'travel.other.expense.line',
        'expense_id',
        string="Other Expenses",
        readonly=True
    )

    total_amount_currency = fields.Monetary(
        compute='_compute_total_amount_currency',
        store=True,
        currency_field='currency_id'
    )

    remaining_balance = fields.Monetary(
        string="Remaining Balance",
        compute="_compute_remaining_balance",
        store=True,
        currency_field='currency_id'
    )

    is_manual_amount = fields.Boolean(default=False)

    @api.depends('total_amount_currency', 'travel_request_id.paid_amount')
    def _compute_remaining_balance(self):
        for rec in self:
            paid = rec.travel_request_id.paid_amount if rec.travel_request_id else 0.0
            rec.remaining_balance = rec.total_amount_currency - paid

    # DUPLICATION_OVERRIDER
    def _compute_duplicate_expense_ids(self):
        for rec in self:
            if rec.travel_request_id:
                rec.duplicate_expense_ids = self.env['hr.expense']
            else:
                super(HrExpense, rec)._compute_duplicate_expense_ids()

    def _check_manager(self):
        if not (
                self.env.user.has_group('employee_travel_requisition.group_travel_officer') or
                self.env.user.has_group('employee_travel_requisition.group_expense_manager_custom')
        ):
            raise ValidationError("You are not allowed to perform this action.")

    # def _check_manager(self):
    #     if (
    #             self.env.user.has_group('employee_travel_requisition.group_expense_user_custom')
    #             and not self.env.user.has_group('employee_travel_requisition.group_expense_manager_custom')
    #     ):
    #         raise ValidationError("You are not allowed to perform this action.")

    # @api.depends('advance_line_ids.unit_price',
    #              'advance_line_ids.quantity',
    #              'advance_line_ids.status')
    # @api.depends('advance_line_ids')
    # def _compute_total_amount_currency(self):
    #     for rec in self:
    #         lines = rec.advance_line_ids.filtered(lambda l: l.status == 'approved')
    #
    #         rec.total_amount_currency = sum(
    #             l.unit_price * l.quantity for l in lines
    #         )

    @api.depends('advance_line_ids')
    def _compute_total_amount_currency(self):
        for rec in self:

            # 🔥 DO NOT OVERRIDE if manually changed
            if rec.is_manual_amount:
                continue

            lines = rec.advance_line_ids.filtered(lambda l: l.status == 'approved')

            rec.total_amount_currency = sum(
                l.unit_price * l.quantity for l in lines
            )

    @api.onchange('advance_line_ids.unit_price', 'advance_line_ids.quantity')
    def _onchange_advance_line_values(self):
        for rec in self:
            total = 0
            for line in rec.advance_line_ids:
                total += line.unit_price * line.quantity
            rec.total_amount_currency = total

    @api.onchange('advance_line_ids')
    def _onchange_advance_line_ids(self):
        """Update total when advance lines are added/removed/changed"""
        for rec in self:
            total = 0
            for line in rec.advance_line_ids:
                total += line.unit_price * line.quantity
            rec.total_amount_currency = total

    def _compute_attachment_count(self):
        for rec in self:

            if not rec.travel_request_id:
                rec.attachment_count = 0
                continue

            travel = rec.travel_request_id

            # Travel detail attachments
            travel_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'travel.detail.line'),
                ('res_id', 'in', travel.travel_detail_line_ids.ids),
            ])

            # Accommodation attachments
            accommodation_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'travel.accommodation.line'),
                ('res_id', 'in', travel.accommodation_line_ids.ids),
            ])

            other_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'travel.other.expense.line'),
                ('res_id', 'in', travel.other_expense_line_ids.ids),
            ])

            # Advance extra attachments
            advance_extra_attachments = travel.advance_line_ids.mapped('extra_attachment_ids')

            all_attachments = (
                    travel_attachments |
                    accommodation_attachments |
                    other_attachments |
                    advance_extra_attachments
            )

            rec.attachment_count = len(all_attachments)

    def action_open_documents(self):
        self.ensure_one()

        if not self.travel_request_id:
            return

        travel = self.travel_request_id

        travel_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'travel.detail.line'),
            ('res_id', 'in', travel.travel_detail_line_ids.ids),
        ])

        accommodation_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'travel.accommodation.line'),
            ('res_id', 'in', travel.accommodation_line_ids.ids),
        ])

        other_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'travel.other.expense.line'),
            ('res_id', 'in', travel.other_expense_line_ids.ids),
        ])

        advance_extra_attachments = travel.advance_line_ids.mapped('extra_attachment_ids')

        all_attachments = (
                travel_attachments |
                accommodation_attachments |
                other_attachments |
                advance_extra_attachments

        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Documents',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', all_attachments.ids)],
        }

    def activity_schedule(self, *args, **kwargs):
        return True

    def action_submit(self):
        _logger.error("🔥 HR.EXPENSE SUBMIT CLICKED")

        res = super(HrExpense, self).action_submit()

        _logger.error("🔥 AFTER SUPER SUBMIT")

        for rec in self:
            if rec.state == 'approved':
                rec.state = 'submitted'

        return res

    def _post(self):
        moves = super()._post()

        for expense in self:
            move = expense.account_move_id

            if move and expense.message_partner_ids:
                move.message_subscribe(
                    partner_ids=expense.message_partner_ids.ids
                )

        return moves

    @api.model_create_multi
    def create(self, vals_list):
        _logger.error("🔥 HR.EXPENSE CREATE HIT")
        expenses = super().create(vals_list)

        return expenses

    def write(self, vals):
        if 'total_amount_currency' in vals:
            vals['is_manual_amount'] = True

        return super().write(vals)

    def action_approve(self):
        for rec in self:

            checked_lines = rec.advance_line_ids.filtered(
                lambda l: l.review_status == 'checked'
            )

            if not checked_lines:
                raise ValidationError(
                    "No Checked lines available for approval."
                )

            # Update total before approval
            rec.total_amount_currency = sum(
                line.unit_price * line.quantity for line in checked_lines
            )

        self._check_manager()
        return super().action_approve()

    # REFUSE
    def action_refuse(self):
        self._check_manager()
        return super().action_refuse()

    # RESET
    def action_reset(self):
        self._check_manager()
        return super().action_reset()

    def action_open_travel_request(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Travel Request',
            'res_model': 'travel.request',
            'view_mode': 'form',
            'res_id': self.travel_request_id.id,
            'target': 'current',
        }

    def _compute_approved_advance_lines(self):
        for rec in self:
            if rec.travel_request_id:

                # ✅ YOUR ORIGINAL LOGIC
                lines = rec.advance_line_ids.filtered(
                    lambda l: l.status == 'approved'
                )

                # Filter checked lines for approved AND posted states
                if rec.state in ('approved', 'paid', 'posted'):
                    lines = lines.filtered(
                        lambda l: l.review_status == 'checked'
                    )

                rec.approved_advance_line_ids = lines

            else:
                rec.approved_advance_line_ids = False

    def _inverse_approved_advance_lines(self):
        for rec in self:
            if not rec.travel_request_id:
                continue

            for line in rec.approved_advance_line_ids:
                if not line.travel_id:
                    line.travel_id = rec.travel_request_id.id

    def action_post(self):
        # 🔐 1. SECURITY CHECK (ONLY MANAGER CAN POST)
        self._check_manager()

        for rec in self:
            checked_lines = rec.advance_line_ids.filtered(
                lambda l: l.review_status == 'checked'
            )
            total = sum(checked_lines.mapped('subtotal'))

            # ✅ USE REMAINING BALANCE INSTEAD OF TOTAL
            remaining = total - (rec.travel_request_id.paid_amount if rec.travel_request_id else 0.0)

            # ✅ Only update price_unit for journal entry — DO NOT touch total_amount_currency
            self.env.cr.execute(
                """UPDATE hr_expense 
                   SET price_unit = %s,
                       total_amount = %s
                   WHERE id = %s""",
                (remaining, remaining, rec.id)
            )
            rec.invalidate_recordset(['price_unit', 'total_amount'])
            # # Force all three fields in DB before journal entry is created
            # self.env.cr.execute(
            #     """UPDATE hr_expense
            #        SET total_amount_currency = %s,
            #            total_amount = %s,
            #            price_unit = %s
            #        WHERE id = %s""",
            #     (total, total, total, rec.id)
            # )
            # rec.invalidate_recordset(['total_amount_currency', 'total_amount', 'price_unit'])

        # 🚫 2. DISABLE ODOO AUTO MAIL + FORCE SUDO
        self = self.with_context(
            mail_create_nosubscribe=True,
            mail_notify_force_send=False,
            tracking_disable=True
        ).sudo()

        # ✅ 3. ORIGINAL ODOO LOGIC (VERY IMPORTANT)
        res = super(HrExpense, self).action_post()

        # 📧 4. YOUR CUSTOM EMAIL + CHATTER
        for rec in self:

            partners = rec.message_partner_ids
            if not partners:
                continue

            emails = [e for e in partners.mapped('email') if e]
            if not emails:
                continue

            email_to = ','.join(emails)

            # 📧 SEND EMAIL
            self.env['mail.mail'].sudo().create({
                'subject': f"Expense Paid - {rec.name}",
                'body_html': f"""
                    <p><b>Expense Paid</b></p>
                    <p>
                    Expense: <b>{rec.name}</b><br/>
                    Employee: <b>{rec.employee_id.name}</b><br/>
                    Amount: <b>{rec.total_amount_currency}</b>
                    </p>
                """,
                'email_to': email_to,
            }).send()

            # 💬 CHATTER MESSAGE
            body = f"""
                <div style="font-family: Arial; font-size: 14px;">
                    <p><b>✅ Expense Paid Notification Sent</b></p>

                    <p>
                        <b>Expense:</b> {rec.name}<br/>
                        <b>Employee:</b> {rec.employee_id.name}<br/>
                        <b>Amount:</b> {rec.total_amount_currency} {rec.currency_id.name}<br/>
                        <b>Date:</b> {rec.date}<br/>
                        <b>Status:</b> Posted → Paid
                    </p>

                    <p>
                        📧 Email successfully sent to:<br/>
                        {', '.join(partners.mapped('name'))}
                    </p>

                    <p>
                        <a href="/web#id={rec.id}&model=hr.expense&view_type=form"
                           style="background-color:#875A7B;color:white;padding:8px 12px;
                           text-decoration:none;border-radius:5px;">
                            View Expense
                        </a>
                    </p>
                </div>
            """

            rec.sudo().message_post(
                body=Markup(body),
                subtype_xmlid="mail.mt_comment",
                message_type="comment",
                partner_ids=partners.ids,
            )

        return res

    def _compute_advance_lines(self):
        for rec in self:
            if rec.travel_request_id:
                rec.advance_line_ids = rec.travel_request_id.advance_line_ids.filtered(
                    lambda l: l.status == 'approved'
                )
            else:
                rec.advance_line_ids = False

    @api.onchange('advance_line_ids')
    def _onchange_advance_line_ids_approve(self):
        for line in self.advance_line_ids:
            line.status = 'approved'


class TravelAccommodationLine(models.Model):
    _name = 'travel.accommodation.line'
    _description = 'Travel Accommodation Line'
    _inherit = ['travel.sync.mixin', 'attachment.chatter.mixin']

    unit_price = fields.Float(string="Approximate Budget")

    travel_id = fields.Many2one(
        'travel.request',
        ondelete='cascade'
    )

    hotel_name = fields.Char(string="Hotel/Stay Name")

    check_in_date = fields.Datetime(string="Check-In Date")

    check_out_date = fields.Datetime(string="Check-Out Date")

    city = fields.Char(string="City")

    booking_reference = fields.Char(string="Booking Reference")

    account_remarks = fields.Text(string="Accounts Remarks")

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string="Attachments",
        domain=[('res_model', '=', 'travel.accommodation.line')]
    )

    days = fields.Integer(
        string="Days",
        compute="_compute_days",
        store=True
    )

    description = fields.Text(string="Description")
    booking_agency = fields.Char(string="Booking Agency")

    def _post_attachments_to_chatter(self):
        self._post_line_attachments_to_chatter(
            'travel.accommodation.line',
            lambda r: f"Hotel: {r.hotel_name} ({r.city})"
        )

    @api.depends('check_in_date', 'check_out_date')
    def _compute_days(self):
        for rec in self:
            if rec.check_in_date and rec.check_out_date:
                rec.days = (rec.check_out_date - rec.check_in_date).days
            else:
                rec.days = 0

    def write(self, vals):
        if self.env.context.get('skip_sync'):
            return super(TravelAccommodationLine, self).write(vals)

        old_data = {}

        for rec in self:
            old_data[rec.id] = {
                field: rec[field]
                for field in vals
                if field in rec._fields
            }

        res = super().write(vals)

        self._sync_to_advance(vals, 'accommodation_line_id')

        for rec in self:
            changes = []

            for field, old_val in old_data.get(rec.id, {}).items():
                new_val = rec[field]

                if old_val == new_val:
                    continue

                field_obj = rec._fields[field]

                if field_obj.type in ['one2many', 'many2many']:
                    continue

                field_label = field_obj.string

                def format_value(value):
                    if hasattr(value, 'display_name'):
                        return value.display_name
                    return value if value not in [False, None] else "—"

                changes.append(
                    f"<li><b>{field_label}</b>: {format_value(old_val)} → {format_value(new_val)}</li>"
                )

            if changes and rec.travel_id:
                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>✏️ Accommodation Updated</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

            # ✅ KEEP attachment logic
            if not self.env.context.get('skip_attachment_log'):
                rec._post_attachments_to_chatter()
            # rec._post_attachments_to_chatter()

        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        product = self.env['product.product'].search(
            [('default_code', '=', 'TRANS & ACC')],
            limit=1
        )

        if not product:
            raise ValidationError("TRANS & ACC product not found.")

        for record in records:
            description = (
                f"Hotel: {record.hotel_name or ''} | "
                f"City: {record.city or ''} | "
                f"Check-In: {record.check_in_date or ''} | "
                f"Check-Out: {record.check_out_date or ''} | "
                f"Ref: {record.booking_reference or ''}"
            )

            self.env['travel.advance.line'].create({
                'travel_id': record.travel_id.id,
                'accommodation_line_id': record.id,
                'expense_id': product.id,
                'description': description,
                'line_description': record.description,
                'unit_price': record.unit_price,
                'line_type': 'accommodation',
            })

        for rec in records:
            if not rec.travel_id:
                continue

            changes = []

            EXCLUDE_FIELDS = [
                'id',
                'create_uid', 'create_date',
                'write_uid', 'write_date',
                'display_name', '__last_update'
            ]

            def format_value(value):
                if hasattr(value, 'display_name'):
                    return value.display_name
                return value if value not in [False, None] else None

            for field, field_obj in rec._fields.items():

                if field in EXCLUDE_FIELDS:
                    continue

                if field_obj.type in ['one2many', 'many2many']:
                    continue

                value = rec[field]

                if not value:
                    continue

                value = format_value(value)

                changes.append(
                    f"<li><b>{field_obj.string}</b>: {value}</li>"
                )

            if changes:
                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>➕ Accommodation Added</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

        # ✅ THIS WAS MISSING
        for rec in records:
            if not self.env.context.get('skip_attachment_log'):
                rec._post_attachments_to_chatter()

        return records


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    travel_doc_type = fields.Selection([
        ('travel', 'Travel'),
        ('accommodation', 'Accommodation'),
        ('other', 'Other')
    ], string="Travel Document Type")

    travel_line_description = fields.Char(
        string="Travel Info",
        compute="_compute_travel_line_description",
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') == 'travel.request':
                if self.env.context.get('default_travel_doc_type'):
                    vals['travel_doc_type'] = self.env.context.get('default_travel_doc_type')

        records = super().create(vals_list)

        # for rec in records:
        #
        #     if not rec.res_id:
        #         continue
        #
        #     travel = False
        #     line_info = ""
        #
        #     # ===============================
        #     # TRAVEL DETAIL LINE
        #     # ===============================
        #     if rec.res_model == 'travel.detail.line':
        #
        #         line = self.env['travel.detail.line'].browse(rec.res_id).exists()
        #
        #         if not line or not line.travel_id:
        #             continue
        #
        #         travel = line.travel_id
        #         line_info = f"From: {line.from_location} → {line.to_location}"
        #
        #     # ===============================
        #     # ACCOMMODATION
        #     # ===============================
        #     elif rec.res_model == 'travel.accommodation.line':
        #
        #         line = self.env['travel.accommodation.line'].browse(rec.res_id).exists()
        #
        #         if not line or not line.travel_id:
        #             continue
        #
        #         travel = line.travel_id
        #         line_info = f"Hotel: {line.hotel_name} ({line.city})"
        #
        #     # ===============================
        #     # OTHER EXPENSE
        #     # ===============================
        #     elif rec.res_model == 'travel.other.expense.line':
        #
        #         line = self.env['travel.other.expense.line'].browse(rec.res_id).exists()
        #
        #         if not line or not line.travel_id:
        #             continue
        #
        #         travel = line.travel_id
        #         line_info = f"Expense: {line.expense_type_id.name}"
        #
        #     else:
        #         continue
        #
        #     # 🔥 COPY TO travel.request (THIS IS WHY PREVIEW WORKS)
        #     new_attachment = rec.copy({
        #         'res_model': 'travel.request',
        #         'res_id': travel.id,
        #     })
        #
        #     # 🔥 POST
        #     travel.message_post(
        #         body=Markup(f"""
        #             <b>📎 Attachment Added</b><br/>
        #             {rec.name}<br/>
        #             <small>{line_info}</small>
        #         """),
        #         attachment_ids=[new_attachment.id],
        #         subtype_xmlid="mail.mt_note"
        #     )

        # # ✅ ADD CHATTER LOGIC
        # for rec in records:
        #     travel = False
        #
        #     if rec.res_model == 'travel.request':
        #         travel = self.env['travel.request'].browse(rec.res_id)
        #
        #     elif rec.res_model == 'travel.detail.line':
        #         line = self.env['travel.detail.line'].browse(rec.res_id)
        #         travel = line.travel_id
        #
        #     elif rec.res_model == 'travel.accommodation.line':
        #         line = self.env['travel.accommodation.line'].browse(rec.res_id)
        #         travel = line.travel_id
        #
        #     elif rec.res_model == 'travel.other.expense.line':
        #         line = self.env['travel.other.expense.line'].browse(rec.res_id)
        #         travel = line.travel_id
        #
        #     attachment = self.env['ir.attachment'].browse(rec.id)
        #
        #     # ✅ POST WITH PREVIEW
        #     if travel and rec.res_id:
        #         # ✅ COPY attachment to travel.request (THIS IS THE FIX)
        #         new_attachment = rec.copy({
        #             'res_model': 'travel.request',
        #             'res_id': travel.id,
        #         })
        #
        #         travel.message_post(
        #             body=Markup(f"""
        #             <b>📎 Attachment Added</b><br/>
        #             {rec.name}<br/>
        #             <small>{rec.travel_line_description or ''}</small>
        #             """),
        #             attachment_ids=[new_attachment.id],  # ✅ USE COPIED ONE
        #             subtype_xmlid="mail.mt_note"
        #         )
        #
        return records

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('res_model') == 'travel.request':
    #             if self.env.context.get('default_travel_doc_type'):
    #                 vals['travel_doc_type'] = self.env.context.get('default_travel_doc_type')
    #     return super().create(vals_list)

    @api.depends('res_model', 'res_id')
    def _compute_travel_line_description(self):
        for rec in self:
            rec.travel_line_description = False

            # ===============================
            # Travel Detail Line
            # ===============================
            if rec.res_model == 'travel.detail.line' and rec.res_id:
                line = self.env['travel.detail.line'].browse(rec.res_id)

                rec.travel_line_description = (
                    f"From: {line.from_location or ''} | "
                    f"To: {line.to_location or ''} | "
                    f"Departure: {line.travel_from or ''} | "
                    f"Return: {line.travel_to or ''} | "
                    f"Mode: {line.travel_mode_id.name or ''}"
                )

            # ===============================
            # Accommodation Line
            # ===============================
            elif rec.res_model == 'travel.accommodation.line' and rec.res_id:
                line = self.env['travel.accommodation.line'].browse(rec.res_id)

                rec.travel_line_description = (
                    f"Hotel: {line.hotel_name or ''} | "
                    f"City: {line.city or ''} | "
                    f"Check-In: {line.check_in_date or ''} | "
                    f"Check-Out: {line.check_out_date or ''}"
                )

            elif rec.res_model == 'travel.other.expense.line' and rec.res_id:
                line = self.env['travel.other.expense.line'].browse(rec.res_id)

                rec.travel_line_description = (
                    f"Expense Type: {line.expense_type_id.name or ''} | "
                    f"Description: {line.description or ''} | "
                    f"Date: {line.expense_date or ''} | "
                    f"Amount: {line.unit_price or 0}"
                )

            # ===============================
            # Advance Line (IMPORTANT FIX)
            # ===============================
            elif rec.res_model == 'travel.advance.line' and rec.res_id:
                line = self.env['travel.advance.line'].browse(rec.res_id)

                rec.travel_line_description = line.description or ''

    # @api.depends('res_model', 'res_id')
    # def _compute_travel_line_description(self):
    #     for rec in self:
    #         rec.travel_line_description = False
    #
    #         # Travel detail line
    #         if rec.res_model == 'travel.detail.line' and rec.res_id:
    #             line = self.env['travel.detail.line'].browse(rec.res_id)
    #
    #             rec.travel_line_description = (
    #                 f"From: {line.from_location or ''} | "
    #                 f"To: {line.to_location or ''} | "
    #                 f"Departure: {line.travel_from or ''} | "
    #                 f"Return: {line.travel_to or ''} | "
    #                 f"Mode: {line.travel_mode_id.name or ''}"
    #                 # f"Mode: {line.travel_mode or ''}"
    #             )
    #
    #         # Accommodation line
    #         elif rec.res_model == 'travel.accommodation.line' and rec.res_id:
    #             line = self.env['travel.accommodation.line'].browse(rec.res_id)
    #
    #             rec.travel_line_description = (
    #                 f"Hotel: {line.hotel_name or ''} | "
    #                 f"City: {line.city or ''} | "
    #                 f"Check-In: {line.check_in_date or ''} | "
    #                 f"Check-Out: {line.check_out_date or ''}"
    #             )


class TravelOtherExpenseLine(models.Model):
    _name = 'travel.other.expense.line'
    _description = 'Travel Other Expense Line'
    _inherit = ['travel.sync.mixin', 'attachment.chatter.mixin']

    unit_price = fields.Float(string="Approximate Budget")

    travel_id = fields.Many2one(
        'travel.request',
        ondelete='cascade'
    )

    expense_type_id = fields.Many2one(
        'travel.expense.type',
        string="Expense Type",
        required=True
    )

    expense_id = fields.Many2one(
        'hr.expense',
        string="Expense",
        ondelete='cascade'
    )

    description = fields.Char(string="Description")
    expense_date = fields.Datetime(string="Date")

    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string="Attachments",
        domain=[('res_model', '=', 'travel.other.expense.line')]
    )

    account_remarks = fields.Text(string="Accounts Remarks")

    def _post_attachments_to_chatter(self):
        self._post_line_attachments_to_chatter(
            'travel.other.expense.line',
            lambda r: f"Expense: {r.expense_type_id.name}"
        )

    def write(self, vals):
        if self.env.context.get('skip_sync'):
            return super(TravelOtherExpenseLine, self).write(vals)

        old_data = {}

        for rec in self:
            old_data[rec.id] = {
                field: rec[field]
                for field in vals
                if field in rec._fields
            }

        res = super().write(vals)

        self._sync_to_advance(vals, 'other_expense_line_id')

        for rec in self:
            changes = []

            for field, old_val in old_data.get(rec.id, {}).items():
                new_val = rec[field]

                if old_val == new_val:
                    continue

                field_obj = rec._fields[field]

                if field_obj.type in ['one2many', 'many2many']:
                    continue

                field_label = field_obj.string

                def format_value(value):
                    if hasattr(value, 'display_name'):
                        return value.display_name
                    return value if value not in [False, None] else "—"

                changes.append(
                    f"<li><b>{field_label}</b>: {format_value(old_val)} → {format_value(new_val)}</li>"
                )

            if changes and rec.travel_id:
                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>✏️ Other Expense Updated</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

            # ✅ KEEP attachment logic
            if not self.env.context.get('skip_attachment_log'):
                rec._post_attachments_to_chatter()
            # rec._post_attachments_to_chatter()

        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        product = self.env['product.product'].search(
            [('default_code', '=', 'TRANS & ACC')],
            limit=1
        )

        if not product:
            raise ValidationError("TRANS & ACC product not found.")

        for record in records:
            description = (
                f"Expense Type: {record.expense_type_id.name or ''} | "
                f"Date: {record.expense_date or ''} | "
                f"Note: {record.description or ''}"
            )

            existing_line = self.env['travel.advance.line'].search([
                ('other_expense_line_id', '=', record.id)
            ], limit=1)

            if not existing_line:
                self.env['travel.advance.line'].create({
                    'travel_id': record.travel_id.id,
                    'other_expense_line_id': record.id,
                    'expense_id': product.id,
                    'description': description,
                    'line_description': record.description,
                    'unit_price': record.unit_price,
                    'line_type': 'other',
                })

        for rec in records:
            if not rec.travel_id:
                continue

            changes = []

            EXCLUDE_FIELDS = [
                'id',
                'create_uid', 'create_date',
                'write_uid', 'write_date',
                'display_name', '__last_update'
            ]

            def format_value(value):
                if hasattr(value, 'display_name'):
                    return value.display_name
                return value if value not in [False, None] else None

            for field, field_obj in rec._fields.items():

                # ❌ skip junk
                if field in EXCLUDE_FIELDS:
                    continue

                # ❌ skip relational noise
                if field_obj.type in ['one2many', 'many2many']:
                    continue

                value = rec[field]

                if not value:
                    continue

                value = format_value(value)

                changes.append(
                    f"<li><b>{field_obj.string}</b>: {value}</li>"
                )

            # for field in rec._fields:
            #     field_obj = rec._fields[field]
            #
            #     if field_obj.type in ['one2many', 'many2many']:
            #         continue
            #
            #     value = rec[field]
            #
            #     if value:
            #         if hasattr(value, 'display_name'):
            #             value = value.display_name
            #
            #         changes.append(
            #             f"<li><b>{field_obj.string}</b>: {value}</li>"
            #         )

            if changes:
                rec.travel_id.sudo().message_post(
                    body=Markup(f"""
                        <b>➕ Other Expense Added</b>
                        <ul>
                            {''.join(changes)}
                        </ul>
                    """),
                    subtype_xmlid="mail.mt_note"
                )

        # ✅ THIS WAS MISSING
        for rec in records:
            if not self.env.context.get('skip_attachment_log'):
                rec._post_attachments_to_chatter()
            # rec._post_attachments_to_chatter()

        return records
