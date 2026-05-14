from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    date_of_joining = fields.Date(string="Date of Joining")

    experience = fields.Char(
        string="Experience",
        compute="_compute_experience",
        store=True
    )

    @api.depends('date_of_joining')
    def _compute_experience(self):
        today = date.today()
        for record in self:
            if record.date_of_joining:
                diff = relativedelta(today, record.date_of_joining)
                years = diff.years
                months = diff.months

                if years > 0:
                    record.experience = f"{years} Year(s) {months} Month(s)"
                else:
                    record.experience = f"{months} Month(s)"
            else:
                record.experience = False

    # ===============================
    # Address Sync
    # ===============================
    address = fields.Char("")

    same_as_private_address = fields.Boolean(string="Same as Private Address")
    alternative_street = fields.Char()
    alternative_street2 = fields.Char()
    alternative_city = fields.Char()
    alternative_state_id = fields.Many2one('res.country.state')
    alternative_zip = fields.Char()
    alternative_country_id = fields.Many2one('res.country')

    @api.onchange('same_as_private_address')
    def _onchange_same_as_private_address(self):
        for rec in self:
            if rec.same_as_private_address:
                rec.alternative_street = rec.private_street
                rec.alternative_street2 = rec.private_street2
                rec.alternative_city = rec.private_city
                rec.alternative_state_id = rec.private_state_id
                rec.alternative_zip = rec.private_zip
                rec.alternative_country_id = rec.private_country_id
            else:
                rec.alternative_street = False
                rec.alternative_street2 = False
                rec.alternative_city = False
                rec.alternative_state_id = False
                rec.alternative_zip = False
                rec.alternative_country_id = False

    # address = fields.Text(string="Address")
    #
    # same_as_private_address = fields.Boolean(
    #     string="Same as Private Address",
    #     tracking=True
    # )
    #
    # @api.onchange(
    #     'same_as_private_address',
    #     'private_street',
    #     'private_street2',
    #     'private_city',
    #     'private_state_id',
    #     'private_zip',
    #     'private_country_id'
    # )
    # def _onchange_same_as_private_address(self):
    #     for rec in self:
    #         if rec.same_as_private_address:
    #             parts = [
    #                 rec.private_street or '',
    #                 rec.private_street2 or '',
    #                 rec.private_city or '',
    #                 rec.private_state_id.name if rec.private_state_id else '',
    #                 rec.private_zip or '',
    #                 rec.private_country_id.name if rec.private_country_id else '',
    #             ]
    #             rec.address = "\n".join(filter(None, parts))
    #         else:
    #             rec.address = False

    # ===============================
    # Contract Details
    # ===============================

    contract_valid_from = fields.Date(string="Contract Valid From", tracking=True)
    contract_valid_to = fields.Date(string="Contract Valid To", tracking=True)

    @api.constrains('contract_valid_from', 'contract_valid_to')
    def _check_contract_dates(self):
        for rec in self:
            if rec.contract_valid_from and rec.contract_valid_to:
                if rec.contract_valid_to < rec.contract_valid_from:
                    raise ValidationError(
                        "Contract Valid To date must be greater than Valid From date."
                    )

    employment_contract = fields.Binary(
        string="Employment Contract",
        attachment=True,
        tracking=True
    )
    employment_contract_filename = fields.Char(string="Employment Contract File Name")

    nda_signed = fields.Boolean(string="NDA Signed", tracking=True)

    nda_details = fields.Binary(
        string="NDA Document",
        attachment=True,
        tracking=True
    )
    nda_details_filename = fields.Char(string="NDA File Name")

    background_check_done = fields.Boolean(string="Background Check Done", tracking=True)
    background_check_notes = fields.Char(string="Background Check Notes", tracking=True)

    work_permit_details = fields.Char(string="Work Permit Details", tracking=True)
    work_permit_expiry = fields.Date(string="Work Permit Expiry", tracking=True)

    # ===============================
    # Performance & Development
    # ===============================

    training_programs = fields.Char(string="Training Programs Attended", tracking=True)
    languages_known = fields.Char(string="Languages Known", tracking=True)

    licences_permits = fields.Char(
        string="Necessary Licences / Permits (with Expiry)",
        tracking=True
    )

    promotions_transfers = fields.Char(
        string="Promotions and Transfers",
        tracking=True
    )

    rating_ids = fields.One2many(
        'hr.employee.rating',
        'employee_id',
        string="Ratings",
        tracking=True
    )

    # ===============================
    # Social Media
    # ===============================

    facebook_id = fields.Char(string="Facebook ID", tracking=True)
    whatsapp_no = fields.Char(string="WhatsApp No", tracking=True)
    linkedin_id = fields.Char(string="LinkedIn ID", tracking=True)
    signal_id = fields.Char(string="Signal", tracking=True)
    x_twitter_id = fields.Char(string="X (Twitter) ID", tracking=True)

    # ===============================
    # Emergency Contact
    # ===============================

    emergency_contact_name = fields.Char(string="Emergency Contact Name", tracking=True)
    emergency_contact_relation = fields.Char(string="Relationship", tracking=True)
    emergency_contact_email = fields.Char(string="Email", tracking=True)
    emergency_contact_address = fields.Text(string="Emergency Contact Address", tracking=True)

    # ===============================
    # Tax & Benefits
    # ===============================

    pan_number = fields.Char(string="PAN Number", tracking=True)
    tax_deduction = fields.Float(string="Tax Deduction", tracking=True)

    health_insurance = fields.Boolean(string="Health Insurance", tracking=True)
    provident_fund = fields.Boolean(string="Provident Fund", tracking=True)
    gratuity = fields.Boolean(string="Gratuity", tracking=True)

    # ===============================
    # Relations
    # ===============================

    previous_employment_ids = fields.One2many(
        'hr.employee.previous.employment',
        'employee_id',
        string='Previous Employment',
        tracking=True
    )

    mentor_id = fields.Many2one(
        'hr.employee',
        string='Mentor',
        tracking=True,
        domain="[('company_id', '=', False), ('company_id', 'in', allowed_company_ids)]"
    )

    education_ids = fields.One2many(
        'hr.employee.education',
        'employee_id',
        string="Educational Background"
    )

    # ===============================
    # Personal Details
    # ===============================

    rfid = fields.Integer(string="RFID", tracking=True)

    first_name = fields.Char(string="First Name", tracking=True)
    middle_name = fields.Char(string="Middle Name", tracking=True)
    last_name = fields.Char(string="Last Name", tracking=True)

    full_name = fields.Char(compute="_compute_full_name", store=True)

    date_of_joining = fields.Date(string="Date of Joining", tracking=True)
    alternative_email = fields.Char(string="Alternative Email", tracking=True)

    blood_group = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-'),
    ], string="Blood Group")

    age = fields.Integer(
        string="Age",
        compute="_compute_age",
        store=True
    )

    # ===============================
    # Compute Methods
    # ===============================

    @api.onchange('user_id')
    def _onchange_user_id_set_name(self):
        if self.user_id:
            self.name = self.user_id.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' not in vals:
                vals['name'] = vals.get('work_email') or 'Employee'
        return super().create(vals_list)

    @api.depends('birthday')
    def _compute_age(self):
        today = date.today()
        for emp in self:
            if emp.birthday:
                emp.age = today.year - emp.birthday.year - (
                        (today.month, today.day) <
                        (emp.birthday.month, emp.birthday.day)
                )
            else:
                emp.age = 0

    def _compute_full_name(self):
        for rec in self:
            rec.full_name = f"{rec.first_name or ''} {rec.last_name or ''}"

    # @api.depends('first_name', 'middle_name', 'last_name')
    # def _compute_full_name(self):
    #     for emp in self:
    #         parts = filter(None, [
    #             emp.first_name,
    #             emp.middle_name,
    #             emp.last_name
    #         ])
    #         emp.full_name = " ".join(parts)
