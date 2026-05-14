{
    "name": "Material Purchase Requisition",
    "version": "19.0.1.0.0",
    "category": "Purchases",
    "summary": "M0–M3 Procurement with Multi-level Approvals",
    "depends": [
        "base",
        "mail",
        "hr",
        "purchase",
        "account",
        'stock'
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",  # Load Access Rights early
        "security/pr_record_rules.xml",
        "data/sequence.xml",
        "data/pr_reminder_config_data.xml",
        'data/mail_template_pr_approval_reminder.xml',
        'data/mail_template_prsubmit_follower_notify.xml',
        'data/rfq_send_notifier.xml',
        'data/mail_template_pr_pending_reminder.xml',
        "data/cron.xml",
        "views/pr_reminder_config_view.xml",  # Views first
        "views/purchase_requisition_tree.xml",
        "views/purchase_requisition_form.xml",
        "views/pr_rfq_wizard.xml",
        "views/alternative_rfq_confirm_wizard.xml",
        "views/purchase_approval_matrix_views.xml",
        "views/pr_menu.xml",  # Menus last
        "views/vendor_evaluation_report_template.xml",
        "views/vendor_evaluation_report.xml",
        "views/purchase_order_vendor_evaluation_views.xml",

        "views/purchase_order_view.xml",

        # "views/pr_reject_wizard_view.xml",
        "views/purchase_requisition_kanban.xml",
        "views/purchase_requisition_calender.xml",
        "views/purchase_requisition_graph.xml",
        "views/purchase_requisition_pivot.xml",
        "views/purchase_order_kanban.xml",
        # "views/purchase_order_buttons.xml",

        "views/menu.xml",
    ],

    "installable": True,
    "application": True,
}
