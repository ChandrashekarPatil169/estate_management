from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # =====================================================
    # IMPACT ON OPERATIONS
    # =====================================================

    affected_users = fields.Many2many(
        'hr.employee',
        string="Affected Users", tracking=True
    )

    affected_users_count = fields.Integer(
        string="Affected Users Count",
        compute="_compute_affected_users_count",
        store=True, tracking=True
    )

    affected_department_id = fields.Many2one(
        'hr.department',
        string="Affected Department", tracking=True
    )

    outage_flag = fields.Boolean(
        string="Service Outage", tracking=True
    )

    @api.depends('affected_users')
    def _compute_affected_users_count(self):
        for rec in self:
            rec.affected_users_count = len(rec.affected_users)

    # =====================================================
    # ASSET / TECHNICAL DETAILS
    # =====================================================

    asset_tag = fields.Char(string="Asset Tag", tracking=True)
    product = fields.Char(string="Product", tracking=True)
    brand = fields.Char(string="Brand", tracking=True)
    model_name = fields.Char(string="Model", tracking=True)
    serial_number = fields.Char(string="Serial Number")
    part_number = fields.Char(string="Part Number", tracking=True)
    purchase_date = fields.Date(string="Purchase Date", tracking=True)
    warranty = fields.Boolean(string="Under Warranty", tracking=True)
    expiry_date = fields.Date(string="Warranty Expiry Date", tracking=True)

    device_name = fields.Char(string="Device Name", tracking=True)
    host = fields.Char(string="Host", tracking=True)
    ip_address = fields.Char(string="IP Address", tracking=True)

    os = fields.Selection([
        ('windows', 'Windows'),
        ('linux', 'Linux'),
        ('mac', 'MacOS'),
        ('android', 'Android'),
        ('ios', 'iOS'),
        ('other', 'Other'),
    ], string="Operating System", tracking=True)

    software_name = fields.Char(string="Software Name", tracking=True)
    error_code = fields.Char(string="Error Code", tracking=True)

    screenshot = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_screenshot_rel',
        'ticket_id',
        'attachment_id',
        string="Screenshot", tracking=True
    )

    steps_to_reproduce = fields.Text(string="Steps to Reproduce", tracking=True)
    last_working_time = fields.Datetime(string="Last Working Time", tracking=True)

    # =====================================================
    # SECURITY & ACCESS
    # =====================================================

    data_sensitivity = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], string="Data Sensitivity", tracking=True)

    security_incident_flag = fields.Boolean(
        string="Security Incident", tracking=True
    )

    requires_approval = fields.Boolean(
        string="Requires Approval", tracking=True
    )

    approval_workflow_id = fields.Many2one(
        'ir.actions.server',
        string="Approval Workflow", tracking=True
    )

    approver_id = fields.Many2one(
        'res.users',
        string="Approver", tracking=True
    )

    approved_at = fields.Datetime(
        string="Approved At", tracking=True
    )

    # =====================================================
    # RESOLUTION
    # =====================================================

    resolution_category = fields.Selection([
        ('config', 'Configuration'),
        ('repair', 'Repair'),
        ('replace', 'Replace'),
        ('workaround', 'Workaround'),
        ('education', 'User Education'),
        ('not_reproduced', 'Not Reproduced'),
    ], string="Resolution Category", tracking=True)

    kb_article_used = fields.Many2one(
        'helpdesk.ticket',
        string="KB Article Used", tracking=True
    )

    root_cause = fields.Text(string="Root Cause", tracking=True)
    preventive_action = fields.Text(string="Preventive Action", tracking=True)
