{
    "name": "Authentication Brute Force Protection",
    "version": "19.0.1.0.0",
    "category": "Tools",
    "summary": "Block IPs after repeated login failures",
    "author": "Shakthi, OCA (adapted), Community",
    "depends": ["base", "web","mail"],
    "data": [
        "security/ir_model_access.xml",
        "views/auth_attempt_views.xml",
        "views/auth_attempt_menu.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "static/src/js/error_handler_patch.js"
        ],
    },

    "license": "LGPL-3",
    "installable": True
}
