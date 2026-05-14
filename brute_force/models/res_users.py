from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

class ResUsers(models.Model):
    _inherit = "res.users"

    def authenticate(self, credential, user_agent_env):
        """Odoo 19 compatible authentication override"""

        ip = None
        login = credential.get("login")

        try:
            ip = request.httprequest.remote_addr
        except Exception:
            pass

        Attempt = self.env["res.authentication.attempt"]

        # ✅ Check block
        if not Attempt.is_allowed(ip, login):
            raise AccessDenied("Too many failed attempts. Try again later.")

        try:
            auth_info = super().authenticate(credential, user_agent_env)

            Attempt.sudo().create({
                "login": login,
                "remote_ip": ip,
                "result": "success"
            })

            return auth_info

        except Exception:
            Attempt.sudo().create({
                "login": login,
                "remote_ip": ip,
                "result": "failed"
            })
            raise

    # @classmethod
    # def authenticate(cls, db, login, password, env):
    #     ip = None
    #
    #     try:
    #         ip = request.httprequest.remote_addr
    #     except Exception:
    #         pass
    #
    #     Attempt = env["res.authentication.attempt"]
    #
    #     if not Attempt.is_allowed(ip, login):
    #         raise AccessDenied("Too many failed attempts.")
    #
    #     try:
    #         uid = super().authenticate(db, login, password, env)
    #         Attempt.create({
    #             "login": login,
    #             "remote_ip": ip,
    #             "result": "success"
    #         })
    #         return uid
    #     except Exception:
    #         Attempt.create({
    #             "login": login,
    #             "remote_ip": ip,
    #             "result": "failed"
    #         })
    #         raise
