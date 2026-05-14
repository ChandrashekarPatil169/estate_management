{
    "name": "RFQ Approval Workflow",
    "version": "1.0",  # Updated to current stable version
    "category": "Inventory/Purchase",  # Standard Odoo category path
    "summary": "Approval workflow for RFQs before Purchase Order confirmation",
    "author": "Internal",
    "license": "LGPL-3",
    "depends": [
        "base",
        "purchase",
        "mail",
        "portal"  # Removed trailing comma
    ],
    "data": [
        # security
        "security/security.xml",
        "security/ir.model.access.csv",


        # 🔥 DEFINE ACTION FIRST
        "views/purchase_approval_team_views.xml",

        # THEN MENUS
        "views/menus.xml",

        # other views
        "views/technical_team_approval_views.xml",
        "views/purchase_order_views.xml",
        "views/template.xml",

        "data/mail_templates.xml",
        "data/mail_template_vendor_rfq_reminder.xml",
        "data/mail_template_po_pending_reminder.xml",
        "data/mail_template_pr_po_confirm.xml",
        "data/mail_template_po_submit_approval.xml",
        "data/cron.xml",
    ],
    "installable": True,
    "application": False,
}
