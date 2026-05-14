from odoo import models, fields


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    # -------------------------
    # Inventory & IT Assets
    # -------------------------

    asset_tag = fields.Char(string="Asset Tag", tracking=True)
    asset_type = fields.Char(string="Asset Type", tracking=True)

    asset_category = fields.Selection([
        ('laptop', 'Laptop'),
        ('desktop', 'Desktop'),
        ('server', 'Server'),
        ('network', 'Network Device'),
        ('printer', 'Printer'),
        ('mobile', 'Mobile'),
        ('other', 'Other'),
    ], string="Asset Category", tracking=True)

    product_name = fields.Char(string="Product Name", tracking=True)
    brand = fields.Char(string="Brand", tracking=True)
    model = fields.Char(string="Model", tracking=True)
    serial_number = fields.Char(string="Serial Number", tracking=True)
    mac_address = fields.Char(string="MAC Address", tracking=True)
    part_number = fields.Char(string="Part Number", tracking=True)

    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned User", tracking=True
    )

    purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Purchase Order", tracking=True
    )

    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        domain="[('move_type','=','in_invoice')]", tracking=True
    )

    warranty_end_at = fields.Date(string="Warranty End Date", tracking=True)

    amc_contract_id = fields.Many2one(
        "purchase.order",
        string="AMC Contract", tracking=True
    )

    # -------------------------
    # Software / License Linkage
    # -------------------------

    related_software_ids = fields.Many2many(
        "product.product",
        string="Related Software", tracking=True
    )

    license_key = fields.Char(string="License Key / Seat ID", tracking=True)

    license_type = fields.Selection([
        ('perpetual', 'Perpetual'),
        ('subscription', 'Subscription'),
        ('named', 'Named'),
        ('concurrent', 'Concurrent'),
    ], string="License Type", tracking=True)

    license_expiry = fields.Date(string="License Expiry", tracking=True)

    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('overused', 'Overused'),
        ('underused', 'Underused'),
    ], string="Compliance Status", tracking=True)

    # -------------------------
    # Resolution & Costs
    # -------------------------

    resolution_notes = fields.Html(string="Resolution Notes", tracking=True)

    resolution_code = fields.Selection([
        ('repaired', 'Repaired'),
        ('replaced', 'Replaced'),
        ('scrapped', 'Scrapped'),
        ('warranty', 'Warranty Claim'),
        ('other', 'Other'),
    ], string="Resolution Code", tracking=True)

    parts_replaced_ids = fields.One2many(
        "helpdesk.ticket.parts",
        "ticket_id",
        string="Parts Replaced", tracking=True
    )

    resolution_cost = fields.Monetary(
        string="Resolution Cost",
        currency_field="currency_id", tracking=True
    )

    chargeback_department_id = fields.Many2one(
        "hr.department",
        string="Chargeback Department", tracking=True
    )

    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id, tracking=True
    )

    service_id = fields.Many2one(
        'helpdesk.service.type',
        string='Service Type', tracking=True
    )


class HelpdeskTicketParts(models.Model):
    _name = "helpdesk.ticket.parts"
    _description = "Helpdesk Ticket Parts"

    ticket_id = fields.Many2one(
        "helpdesk.ticket",
        ondelete="cascade", tracking=True
    )

    item = fields.Char(string="Item", required=True, tracking=True)
    qty = fields.Float(string="Quantity", default=1.0, tracking=True)
    cost = fields.Float(string="Cost", tracking=True)


class HelpdeskServiceManagmentType(models.Model):
    _name = 'helpdesk.service.type'
    _description = 'Helpdesk service type'

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Integer(default=10, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

