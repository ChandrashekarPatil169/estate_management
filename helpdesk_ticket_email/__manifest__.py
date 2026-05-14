{
    'name': 'Helpdesk Ticket Flow',
    'version': '1.0',
    'summary': 'Custom Helpdesk Flow with Submit Button',
    'author': 'Nithya',
    'depends': ['helpdesk_mgmt'],
    'data': [
        'data/mail_template.xml',
        'data/helpdesk_stage.xml',
        'views/helpdesk_ticket_view.xml',
    ],
    'installable': True,
    'application': False,
}
