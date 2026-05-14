from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.database import Database


class WebClientSecurityPatch(http.Controller):

    @http.route('/web/webclient/version_info', type='jsonrpc', auth="none")
    def version_info(self, **kwargs):
        # 🔒 Block version disclosure
        return {
            "error": "Access Denied"
        }



class SecureDatabaseManager(Database):

    @http.route('/web/database/manager', type='http', auth="user")
    def database_manager(self, **kw):
        """
        🛡️ Production-Grade Security:
        Check if the user is a System Administrator before showing the manager.
        """
        # Step 1: Identity check
        if not request.env.user.has_group('base.group_system'):
            return "<html><body><h1>403 Forbidden</h1><p>Access Denied: System Administrators only.</p></body></html>"

        # Step 2: Call the correct Odoo 19 parent method
        # In Odoo 19, the management interface logic is in the 'manager' method.
        return self.manager(**kw)

    @http.route('/web/webclient/version_info', type='jsonrpc', auth="none")
    def version_info(self, **kwargs):
        # 🔒 Block version disclosure
        return {"error": "Access Denied"}