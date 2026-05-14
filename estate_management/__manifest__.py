{
    'name': 'Estate Management',
    'version': '1.0',
    'summary': 'Manage Properties, Buildings, Floors, Units, Rooms, Employees, and Farms',
    'author': 'Innspark',
    'category': 'Real Estate / Farm Management',
    'depends': ['base','mail', 'hr', 'stock', 'contacts','custom_location'],  # HR for employee selection
    'data': [
        # 'security/estate_security.xml',  # Groups
        # 'security/estate_rules.xml',  # Record rules for Estate User
        # 'security/ir.model.access.csv',
        'security/estate_groups_main.xml',
        'security/estate_rules_main.xml',
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/cron.xml',

        # Actions
        'views/actions.xml',

        # Menus
        'views/Miscellanous_views.xml',
        'views/menu.xml',

        # Property / Building / Floor / Unit / Room / Employee
        'views/location_views.xml',

        'views/property_views.xml',
        'views/building_views.xml',
        'views/floor_views.xml',
        'views/unit_views.xml',
        'views/room_views.xml',
        'views/room_employee_views.xml',

        # Maintenance Requests
        'views/maintenance_request_views.xml',

        # Farm Module Views
        'views/farm_views.xml',        
        'views/farm_task_views.xml',
        'views/livestock_views.xml',
        'views/asset_views.xml',
        # Payments
        'views/unit_payment_views.xml',

        # 🔹 Mail Template & Cron Job for Due Payments
        'data/estate_unit_payment_mail_template.xml',
        'data/estate_unit_payment_cron.xml',
        'data/cron_payment_reminder.xml',
        'data/unit_payment_cron.xml',

    ],
    "assets": {
        "web.assets_backend": [
            # "crm_tender_management/static/src/css/error_styles.css",
            "estate_management/static/src/js/error_handler_patch.js",
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}



# ,'brute_force'



