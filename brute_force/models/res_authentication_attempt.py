from odoo import models, fields
from datetime import timedelta
import ipaddress
import logging

_logger = logging.getLogger(__name__)

class ResAuthenticationAttempt(models.Model):
    _name = "res.authentication.attempt"
    _description = "Authentication Attempt Log"
    _order = "create_date desc"

    login = fields.Char(index=True)
    remote_ip = fields.Char(index=True)

    result = fields.Selection([
        ("success", "Success"),
        ("failed", "Failed"),
        ("banned", "Banned"),
        ("unbanned", "Unbanned"),
    ], default="failed", index=True)

    def _is_whitelisted(self, ip):
        param = self.env["ir.config_parameter"].sudo().get_param(
            "auth_bruteforce.whitelist", ""
        )
        nets = param.split(",") if param else []

        for net in nets:
            try:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(net):
                    return True
            except Exception:
                continue
        return False

    def _fail_count(self, ip, login):
        domain = [
            ("remote_ip", "=", ip),
            ("login", "=", login),
        ]

        last_good = self.search(
            domain + [("result", "in", ["success", "unbanned"])],
            order="id desc",
            limit=1
        )

        if last_good:
            domain.append(("id", ">", last_good.id))

        return self.search_count(domain + [("result", "!=", "success")])

    # def is_allowed(self, ip, login):
    #     if not ip:
    #         return True
    #
    #     if self._is_whitelisted(ip):
    #         return True
    #
    #     max_attempts = int(
    #         self.env["ir.config_parameter"].sudo().get_param(
    #             "auth_bruteforce.max_by_ip_login", 5
    #         )
    #     )
    #
    #     fails = self._fail_count(ip, login)
    #
    #     if fails >= max_attempts:
    #         self.create({
    #             "remote_ip": ip,
    #             "login": login,
    #             "result": "banned"
    #         })
    #         return False
    #
    #     return True
    def is_allowed(self, ip, login):
        if not ip:
            return True

        if self._is_whitelisted(ip):
            return True

        ICP = self.env["ir.config_parameter"].sudo()

        max_attempts = int(ICP.get_param("auth_bruteforce.max_by_ip_login", 5))
        block_minutes = int(ICP.get_param("auth_bruteforce.block_minutes", 2))

        domain = [
            ("remote_ip", "=", ip),
            ("login", "=", login),
        ]

        # Get recent failed attempts
        attempts = self.search(domain, order="id desc", limit=max_attempts)

        failed_attempts = [a for a in attempts if a.result == "failed"]

        if len(failed_attempts) >= max_attempts:
            last_attempt = failed_attempts[0]

            block_until = last_attempt.create_date + timedelta(minutes=block_minutes)

            if fields.Datetime.now() < block_until:
                return False

        return True