from odoo import models, fields, api


class HelpdeskTicketReference(models.Model):
    _name = 'helpdesk.ticket.reference'
    _description = 'Ticket Reference Master'
    _rec_name = 'code'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)


# =====================================================
# PROJECT
# =====================================================
class ProjectProject(models.Model):
    _name = 'project.project.custom'
    _inherit = ['mail.thread', 'estate.hierarchy.mixin', 'estate.security.mixin']
    _rec_name = 'project_code'

    name = fields.Char(required=True, tracking=True, string="Project Name")
    project_code = fields.Char(required=True, tracking=True, string='Project Code')

    partner_id = fields.Many2one('res.partner', required=True, tracking=True)

    company_id = fields.Many2one('res.company', tracking=True)

    customer_company_id = fields.Many2one('res.partner', string="Company")
    address = fields.Text(string="Address")

    hdown_subproject_ids = fields.Many2many('project.subproject', string="Subprojects")
    hcount_subproject = fields.Integer(compute='_compute_hcounts', store=True)

    # 🔥 CLEAN ADDRESS
    def _get_clean_address(self, partner):
        return "\n".join(filter(None, [
            partner.street,
            partner.street2,
            " ".join(filter(None, [partner.city, partner.zip])),
            partner.state_id.name if partner.state_id else False,
            partner.country_id.name if partner.country_id else False,
        ]))

    @api.depends('hdown_subproject_ids')
    def _compute_hcounts(self):
        for rec in self:
            rec.hcount_subproject = len(rec.hdown_subproject_ids)

    # def haction_open_subprojects(self):
    #     return self._open_hdown(
    #         'Subprojects',
    #         'project.subproject',
    #         self.hdown_subproject_ids,
    #         {
    #             'default_hup_project_id': self.id,
    #             'default_project_code': self.project_code,
    #             'default_partner_id': self.partner_id.id,
    #         }
    #     )
    def haction_open_subprojects(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subprojects',
            'res_model': 'project.subproject',
            'view_mode': 'list,kanban,form,pivot',
            'domain': [('id', 'in', self.hdown_subproject_ids.ids)],
            'context': {
                'default_hup_project_id': self.id,
                'default_project_code': self.project_code,
                'default_partner_id': self.partner_id.id,
            }
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if not rec.partner_id:
                rec.customer_company_id = False
                rec.address = False
                return

            partner = rec.partner_id
            company_partner = partner.parent_id or partner

            rec.customer_company_id = company_partner.id
            rec.address = rec._get_clean_address(partner)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_id = vals.get('partner_id')
            if partner_id:
                partner = self.env['res.partner'].browse(partner_id)
                company_partner = partner.parent_id or partner

                vals['customer_company_id'] = company_partner.id
                vals['address'] = "\n".join(filter(None, [
                    partner.street,
                    partner.street2,
                    " ".join(filter(None, [partner.city, partner.zip])),
                    partner.state_id.name if partner.state_id else False,
                    partner.country_id.name if partner.country_id else False,
                ]))
        return super().create(vals_list)


# =====================================================
# SUBPROJECT
# =====================================================
class ProjectSubproject(models.Model):
    _name = 'project.subproject'
    _inherit = ['mail.thread', 'estate.hierarchy.mixin', 'estate.security.mixin']
    _rec_name = 'subproject_code'

    name = fields.Char(required=True, tracking=True, string="Subproject Name")
    subproject_code = fields.Char(required=True, tracking=True, string="Subproject Code")

    hup_project_id = fields.Many2one('project.project.custom', required=True, string="Project")
    project_code = fields.Char(related='hup_project_id.project_code', store=True)

    partner_id = fields.Many2one('res.partner', required=True)

    company_id = fields.Many2one('res.company')

    customer_company_id = fields.Many2one('res.partner', string="Company")
    address = fields.Text(string="Address")

    hdown_ticket_ids = fields.Many2many('helpdesk.ticket', string="Tickets")
    hcount_ticket = fields.Integer(compute='_compute_hcounts')
    assigned_ticket_count = fields.Integer(compute='_compute_ticket_counts', store=True)
    resolved_ticket_count = fields.Integer(compute='_compute_ticket_counts', store=True)
    completed_ticket_count = fields.Integer(compute='_compute_ticket_counts', store=True)

    @api.depends('hdown_ticket_ids', 'hdown_ticket_ids.stage_id', 'hdown_ticket_ids.assign_to')
    def _compute_ticket_counts(self):

        for rec in self:

            assigned = 0
            resolved = 0
            completed = 0

            for ticket in rec.hdown_ticket_ids:

                stage_name = (ticket.stage_id.name or '').lower()

                # ✅ DONE (highest priority)
                if 'done' in stage_name:
                    completed += 1

                # ✅ RESOLVED
                elif 'resolved' in stage_name:
                    resolved += 1

                # ✅ ASSIGNED (only if not above states)
                elif ticket.assign_to:
                    assigned += 1

            rec.assigned_ticket_count = assigned
            rec.resolved_ticket_count = resolved
            rec.completed_ticket_count = completed

    def _get_clean_address(self, partner):
        return "\n".join(filter(None, [
            partner.street,
            partner.street2,
            " ".join(filter(None, [partner.city, partner.zip])),
            partner.state_id.name if partner.state_id else False,
            partner.country_id.name if partner.country_id else False,
        ]))

    @api.depends('hdown_ticket_ids')
    def _compute_hcounts(self):
        for rec in self:
            rec.hcount_ticket = len(rec.hdown_ticket_ids)

    # def haction_open_tickets(self):
    #     return self._open_hdown(
    #         'Tickets',
    #         'helpdesk.ticket',
    #         self.hdown_ticket_ids,
    #         {
    #             'default_hup_project_id': self.hup_project_id.id,
    #             'default_hup_subproject_id': self.id,
    #             'default_partner_id': self.partner_id.id,
    #         }
    #     )
    def haction_open_tickets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tickets',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,kanban,form,pivot',
            'domain': [('id', 'in', self.hdown_ticket_ids.ids)],
            'context': {
                'default_hup_project_id': self.hup_project_id.id,
                'default_hup_subproject_id': self.id,
                'default_partner_id': self.partner_id.id,
                'is_external_ticket': True,
            }
        }

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self:
            if not rec.partner_id:
                rec.customer_company_id = False
                rec.address = False
                return

            partner = rec.partner_id
            company_partner = partner.parent_id or partner

            rec.customer_company_id = company_partner.id
            rec.address = rec._get_clean_address(partner)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.hup_project_id:
                rec._add_to_parent(rec.hup_project_id, 'hdown_subproject_ids')

            if rec.hup_project_id and not rec.partner_id:
                rec.partner_id = rec.hup_project_id.partner_id.id

        return records


# =====================================================
# TICKET
# =====================================================
class HelpdeskTicket(models.Model):
    _inherit = ['helpdesk.ticket', 'estate.hierarchy.mixin']

    hup_project_id = fields.Many2one('project.project.custom', string='Project')
    hup_subproject_id = fields.Many2one('project.subproject', string='Subproject')

    project_code = fields.Char(related='hup_project_id.project_code', store=True)
    subproject_code = fields.Char(related='hup_subproject_id.subproject_code', store=True)

    partner_id = fields.Many2one('res.partner')
    company_id = fields.Many2one('res.company')

    address = fields.Text()

    # ✅ CUSTOMER
    customer_partner_id = fields.Many2one('res.partner')
    customer_company_id = fields.Many2one('res.partner')
    customer_address = fields.Text()
    ticket_reference_id = fields.Many2one(
        'helpdesk.ticket.reference',
        string="Ticket Reference",
        tracking=True
    )
    severity_level = fields.Selection(
        [
            ('s1', 'S1 - Critical'),
            ('s2', 'S2 - High'),
            ('s3', 'S3 - Medium'),
        ],
        string="Severity Level",
        tracking=True
    )

    support_level = fields.Selection(
        [
            ('l1', 'L1 - Basic'),
            ('l2', 'L2 - Advanced'),
            ('l3', 'L3 - Expert'),
            ('l4', 'L4 - Specialist'),
        ],
        string="Support Level",
        tracking=True
    )

    # 🔥 CLEAN ADDRESS
    def _get_clean_address(self, partner):
        return "\n".join(filter(None, [
            partner.street,
            partner.street2,
            " ".join(filter(None, [partner.city, partner.zip])),
            partner.state_id.name if partner.state_id else False,
            partner.country_id.name if partner.country_id else False,
        ]))

    @api.onchange('customer_partner_id')
    def _onchange_customer_partner_id(self):
        for rec in self:
            if not rec.customer_partner_id:
                rec.customer_company_id = False
                rec.customer_address = False
                return

            partner = rec.customer_partner_id
            company_partner = partner.parent_id or partner

            rec.customer_company_id = company_partner.id
            rec.customer_address = rec._get_clean_address(partner)

    def _apply_hierarchy(self):
        for rec in self:
            if rec.hup_subproject_id and not rec.hup_project_id:
                rec.hup_project_id = rec.hup_subproject_id.hup_project_id.id

            if rec.hup_subproject_id:
                rec._add_to_parent(rec.hup_subproject_id, 'hdown_ticket_ids')

    @api.model_create_multi
    def create(self, vals_list):

        # =========================
        # STEP 1: PREPARE VALUES
        # =========================
        for vals in vals_list:

            # ✅ COMPANY
            if not vals.get('company_id'):
                vals['company_id'] = self.env.company.id

            # ✅ ASSIGN
            if vals.get('assign_to'):
                vals['assign_date'] = fields.Datetime.now()
                vals['user_id'] = vals.get('assign_to')

        # =========================
        # STEP 2: CREATE
        # =========================
        records = super().create(vals_list)

        # =========================
        # STEP 3: FORCE SEQUENCE
        # =========================
        for rec in records:

            if rec.hup_project_id and rec.hup_subproject_id and rec.ticket_reference_id:

                prefix = f"{rec.ticket_reference_id.code}/{rec.hup_project_id.project_code}/{rec.hup_subproject_id.subproject_code}/"

                # 🔥 LOCK TABLE (prevents duplicate in multi-user)
                self.env.cr.execute("LOCK TABLE helpdesk_ticket IN EXCLUSIVE MODE")

                last_ticket = self.search(
                    [
                        ('number', 'like', f'{prefix}%'),
                        ('id', '!=', rec.id)
                    ],
                    order='id desc',  # safer than number desc
                    limit=1
                )

                if last_ticket and last_ticket.number:
                    try:
                        last_seq = int(last_ticket.number.split('/')[-1])
                        next_seq = last_seq + 1
                    except:
                        next_seq = 1
                else:
                    next_seq = 1

                new_number = f"{prefix}{str(next_seq).zfill(3)}"

                rec.sudo().write({'number': new_number})

        # =========================
        # STEP 4: OTHER LOGIC
        # =========================
        for rec in records:

            rec._apply_hierarchy()

            if rec.customer_partner_id:
                partner = rec.customer_partner_id
                company_partner = partner.parent_id or partner

                rec.customer_company_id = company_partner.id
                rec.customer_address = rec._get_clean_address(partner)

        return records



    def write(self, vals):
        res = super().write(vals)
        self._apply_hierarchy()
        return res

    def _generate_ticket_number(self, vals):
        project_id = vals.get('hup_project_id')
        subproject_id = vals.get('hup_subproject_id')

        if not project_id or not subproject_id:
            return False

        project = self.env['project.project.custom'].browse(project_id)
        subproject = self.env['project.subproject'].browse(subproject_id)

        prefix = f"{project.project_code}/{subproject.subproject_code}/"

        # 🔥 SEARCH LAST TICKET FROM DB
        last_ticket = self.search(
            [('number', 'like', f'{prefix}%')],
            order='number desc',
            limit=1
        )

        if last_ticket and last_ticket.number:
            try:
                last_seq = int(last_ticket.number.split('/')[-1])
                next_seq = last_seq + 1
            except:
                next_seq = 1
        else:
            next_seq = 1

        return f"{prefix}{str(next_seq).zfill(3)}"

# PERFECT
# from odoo import models, fields, api
#
#
# # =====================================================
# # PROJECT
# # =====================================================
# class ProjectProject(models.Model):
#     _name = 'project.project.custom'
#     _inherit = ['mail.thread', 'estate.hierarchy.mixin', 'estate.security.mixin']
#     _rec_name = 'project_code'
#     name = fields.Char(required=True, tracking=True,string="Project Name")
#     project_code = fields.Char(required=True, tracking=True,string='Project Code')
#
#     partner_id = fields.Many2one('res.partner', required=True, tracking=True)
#
#     # ✅ SYSTEM FIELD (DO NOT TOUCH LOGIC)
#     company_id = fields.Many2one('res.company', tracking=True)
#
#     # ✅ BUSINESS FIELDS
#     customer_company_id = fields.Many2one('res.partner', string="Company")
#     address = fields.Text(string="Address")
#
#     hdown_subproject_ids = fields.Many2many('project.subproject', string="Subprojects")
#
#     hcount_subproject = fields.Integer(compute='_compute_hcounts')
#
#     @api.depends('hdown_subproject_ids')
#     def _compute_hcounts(self):
#         for rec in self:
#             rec.hcount_subproject = len(rec.hdown_subproject_ids)
#
#     def haction_open_subprojects(self):
#         return self._open_hdown(
#             'Subprojects',
#             'project.subproject',
#             self.hdown_subproject_ids,
#             {
#                 'default_hup_project_id': self.id,
#                 'default_project_code': self.project_code,
#                 'default_partner_id': self.partner_id.id,
#             }
#         )
#
#     @api.onchange('partner_id')
#     def _onchange_partner_id(self):
#         for rec in self:
#             if not rec.partner_id:
#                 rec.customer_company_id = False
#                 rec.address = False
#                 return
#
#             partner = rec.partner_id
#             company_partner = partner.parent_id or partner
#
#             rec.customer_company_id = company_partner.id
#             rec.address = partner.contact_address
#
#     @api.model_create_multi
#     def create(self, vals_list):
#
#         for vals in vals_list:
#             partner_id = vals.get('partner_id')
#
#             if partner_id:
#                 partner = self.env['res.partner'].browse(partner_id)
#                 company_partner = partner.parent_id or partner
#
#                 vals['customer_company_id'] = company_partner.id
#                 vals['address'] = partner.contact_address
#
#         return super().create(vals_list)
#
#
#
#
# # =====================================================
# # SUBPROJECT
# # =====================================================
# class ProjectSubproject(models.Model):
#     _name = 'project.subproject'
#     _inherit = ['mail.thread', 'estate.hierarchy.mixin', 'estate.security.mixin']
#     _rec_name = 'subproject_code'
#
#     name = fields.Char(required=True, tracking=True,string="Subproject Name")
#     subproject_code = fields.Char(required=True, tracking=True,string="Subproject Code")
#
#     hup_project_id = fields.Many2one('project.project.custom', required=True,string="Project")
#
#     project_code = fields.Char(related='hup_project_id.project_code', store=True)
#
#     partner_id = fields.Many2one('res.partner', required=True)
#
#     # ✅ SYSTEM SAFE
#     company_id = fields.Many2one('res.company')
#
#     # ✅ BUSINESS
#     customer_company_id = fields.Many2one('res.partner', string="Company")
#     address = fields.Text(string="Address")
#
#     hdown_ticket_ids = fields.Many2many('helpdesk.ticket', string="Tickets")
#
#     hcount_ticket = fields.Integer(compute='_compute_hcounts')
#
#     @api.depends('hdown_ticket_ids')
#     def _compute_hcounts(self):
#         for rec in self:
#             rec.hcount_ticket = len(rec.hdown_ticket_ids)
#
#     def haction_open_tickets(self):
#         return self._open_hdown(
#             'Tickets',
#             'helpdesk.ticket',
#             self.hdown_ticket_ids,
#             {
#                 'default_hup_project_id': self.hup_project_id.id,
#                 'default_hup_subproject_id': self.id,
#                 'default_partner_id': self.partner_id.id,
#             }
#         )
#
#     @api.onchange('partner_id')
#     def _onchange_partner_id(self):
#         for rec in self:
#             if not rec.partner_id:
#                 rec.customer_company_id = False
#                 rec.address = False
#                 return
#
#             partner = rec.partner_id
#             company_partner = partner.parent_id or partner
#
#             rec.customer_company_id = company_partner.id
#             rec.address = partner.contact_address
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         records = super().create(vals_list)
#
#         for rec in records:
#
#             if rec.hup_project_id:
#                 rec._add_to_parent(rec.hup_project_id, 'hdown_subproject_ids')
#
#             if rec.hup_project_id and not rec.partner_id:
#                 rec.partner_id = rec.hup_project_id.partner_id.id
#
#         return records
#
#
# # =====================================================
# # TICKET
# # =====================================================
# class HelpdeskTicket(models.Model):
#     _inherit = ['helpdesk.ticket', 'estate.hierarchy.mixin']
#
#     hup_project_id = fields.Many2one('project.project.custom',string='Project')
#     hup_subproject_id = fields.Many2one('project.subproject',string='Subproject')
#
#     project_code = fields.Char(related='hup_project_id.project_code', store=True)
#     subproject_code = fields.Char(related='hup_subproject_id.subproject_code', store=True)
#
#     partner_id = fields.Many2one('res.partner')
#
#     # ✅ SYSTEM SAFE
#     company_id = fields.Many2one('res.company')
#
#     address = fields.Text()
#
#     # ✅ CUSTOMER
#     customer_partner_id = fields.Many2one('res.partner')
#     customer_company_id = fields.Many2one('res.partner')
#     customer_address = fields.Text()
#
#     @api.onchange('customer_partner_id')
#     def _onchange_customer_partner_id(self):
#         for rec in self:
#             if not rec.customer_partner_id:
#                 rec.customer_company_id = False
#                 rec.customer_address = False
#                 return
#
#             partner = rec.customer_partner_id
#             company_partner = partner.parent_id or partner
#
#             rec.customer_company_id = company_partner.id
#             rec.customer_address = partner.contact_address
#
#     def _apply_hierarchy(self):
#         for rec in self:
#             if rec.hup_subproject_id and not rec.hup_project_id:
#                 rec.hup_project_id = rec.hup_subproject_id.hup_project_id.id
#
#             if rec.hup_subproject_id:
#                 rec._add_to_parent(rec.hup_subproject_id, 'hdown_ticket_ids')
#
#     @api.model_create_multi
#     def create(self, vals_list):
#
#         for vals in vals_list:
#             if not vals.get('company_id'):
#                 vals['company_id'] = self.env.company.id
#
#         records = super().create(vals_list)
#
#         for rec in records:
#             rec._apply_hierarchy()
#
#             if rec.customer_partner_id:
#                 partner = rec.customer_partner_id
#                 company_partner = partner.parent_id or partner
#
#                 rec.customer_company_id = company_partner.id
#                 rec.customer_address = partner.contact_address
#
#         return records
#
#     def write(self, vals):
#         res = super().write(vals)
#         self._apply_hierarchy()
#         return res
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
