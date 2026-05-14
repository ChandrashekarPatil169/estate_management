{
    'name': 'Estate Coffee Management',
    'version': '1.0',
    'summary': 'Manage Coffee Machines, Stock, Refills, and Cleaning',
    'description': 'Coffee Machine Management integrated with Estate Management',
    'author': 'Innspark',
    'category': 'Miscellaneous',
    'depends': ['base', 'hr', 'estate_management','uom'],
    'data': [
        # Security
        # 'security/security.xml',             # Groups
        # 'security/ir.model.access.csv',      # Model Access
        # 'security/coffee_rules.xml',         # Record Rules
        'security/coffee_security_groups.xml',  # Groups
        'security/ir.model.access.csv',  # Model Access
        'security/coffee_security_rules.xml',  # Record Rules

        # Views
        'views/coffee_ingredient_views.xml',
        'views/building_stock_views.xml',
        'views/coffee_machine_views.xml',
        'views/coffee_purchase_views.xml',
        'views/machine_stock_views.xml',
        'views/cleaning_log_views.xml',

        # Actions first, then Menus
        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
}
