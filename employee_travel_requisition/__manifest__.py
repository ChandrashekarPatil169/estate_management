{
    'name': 'Employee Travel Requisition',
    'version': '19.0.1.0.0',
    'summary': 'Employee Travel Requisition Management',
    'category': 'Human Resources',
    'author': 'Your Name',
    'depends': [
        'base',
        'mail',
        'hr',
        'project',
        'analytic',
        'account',
        'product',
        'uom',
        'hr_expense',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',

        'data/sequence.xml',
        'data/mail_templates.xml',

        # FIRST load views where action is defined
        'views/travel_request_views.xml',
        'views/expenses_type_master.xml',

        # THEN load menu that references that action
        'views/travel_menu.xml',
    ],
    'installable': True,
    'application': True,
}
