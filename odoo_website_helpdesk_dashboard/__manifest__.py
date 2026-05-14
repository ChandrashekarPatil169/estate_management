{
    'name': "Website HelpDesk Dashboard",
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': """Helpdesk Support Ticket Management Dashboard""",
    'description': """Website HelpDesk Dashboard Module Brings a Multipurpose"""
                   """Graphical Dashboard for Website HelpDesk module""",
    'author': "My Company",
    'company': 'My Company',
    'countries': ['IN'],
    'depends': ['helpdesk_mgmt', 'base', 'department_helpdesk'],
    'data': [
        'security/security_groups.xml',
        'views/menu_item.xml',
        'views/dashboard_templates.xml',
        'views/res_users_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo_website_helpdesk_dashboard/static/src/css/dashboard.css',
            'odoo_website_helpdesk_dashboard/static/src/js/lib/Chart.bundle.js',
            'odoo_website_helpdesk_dashboard/static/src/js/dashboard_view.js',
            'odoo_website_helpdesk_dashboard/static/src/xml/dashboard_view.xml',
            'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js'
        ],
    },
    'license': 'LGPL-3',
    'auto_install': False,
    'installable': True,
    'application': False,
}
