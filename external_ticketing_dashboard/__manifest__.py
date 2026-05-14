{
    'name': "External Ticketing Dashboard",
    'version': '19.0.1.0.0',
    'category': 'Helpdesk',
    'summary': "Dashboard for External Ticketing — Projects, Subprojects & Tickets",
    'description': """
        Adds a website-style dashboard for the External Ticketing menu inside Department Helpdesk.
        Shows counts, priority breakdown, project/subproject stats, and charts.
    """,
    'author': 'My Company',
    'company': 'My Company',
    'depends': [
        'base',
        'department_helpdesk',
        'helpdesk_mgmt',
        'odoo_website_helpdesk_dashboard',
    ],
    'data': [
        'security/security_groups.xml',
        'views/menu_item.xml',
        'views/dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'external_ticketing_dashboard/static/src/css/ext_dashboard.css',
            'external_ticketing_dashboard/static/src/js/ext_dashboard_view.js',
            'external_ticketing_dashboard/static/src/xml/ext_dashboard_view.xml',
        ],
    },
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False,
}
