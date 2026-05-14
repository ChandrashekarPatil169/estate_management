{
    "name": "Project Tabs",
    "version": "1.0",
    "category": "Project",
    "summary": "Manage different Tabs in a Project module",
    "author": "Kiran",
    "description": """
            - Smart button and tab view
            - Safe deletion rules
            """,
    "depends": [ "project",'calendar', 'hr',"project_main_mgmt",
    'contacts',"mail"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template.xml",
        "views/project_kanban.xml",
        "views/project_project_form_tabs.xml",
        "views/charter_approval_config_view.xml",
        "views/project_risk_views.xml",
    ],
    "installable": True,
    "application": False,
}
