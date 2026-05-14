# Copyright 2016-2024 Tecnativa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Project Timeline",
    "summary": "Timeline view for projects",
    "version": "19.0.1.0.0",
    "category": "Project Management",
    "license": "AGPL-3",
    "depends": [
        "project",
        "web_timeline",
        "project_main_mgmt",
    ],
    "data": [
        "views/project_project_view.xml",
        "views/project_task_view.xml",
    ],
    "demo": [
        "demo/project_project_demo.xml",
        "demo/project_task_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "project_timeline/static/src/scss/project_timeline.scss",
        ],
    },
    "development_status": "Production/Stable",
    "maintainers": ["tarteo"],
    "installable": True,
    "application": False,
}