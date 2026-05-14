{
    'name': 'Custom Location',
    "version": "19.0.1",  # Ensure this matches your Odoo version
    'author': 'Your Company',  # Replace with your actual company or name
    'category': 'Tools',
    'depends': ['base', 'web', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/location_template.xml',
    ],
    'assets': {
    'web.assets_backend': [
        'custom_location/static/src/js/location.js',
        'custom_location/static/src/xml/location.xml',
    ],
},
    'installable': True,
    'application': True,
    'license': 'LGPL-3',  # Correct the typo here
}
