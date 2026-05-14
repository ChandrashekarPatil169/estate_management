{
    'name': 'Estate DG Management',
    'version': '1.0',
    'summary': 'Manage Diesel Generators, Fuel Purchases, Refills, and Logs in the Estate',
    'category': 'Operations',
    'author': 'Your Name',
    'depends': ['base', 'estate_management'],
    'data': [
        # Security
        'security/dg_groups.xml',
        'security/ir.model.access.csv',
        'security/dg_security_rules.xml',


        # Core DG model views (load views before actions!)
        'views/estate_dg_views.xml',

        # Purchases
        'views/estate_dg_purchase_views.xml',

        # Refills
        'views/estate_dg_refill_views.xml',

        # Logs (daily usage)
        'views/estate_dg_log_views.xml',

        # Actions (after views)
        'views/estate_dg_action.xml',

        # Menus
        'views/estate_dg_menu.xml',
    ],
    'installable': True,
    'application': False,
}
