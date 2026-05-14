from odoo import models
import logging
_logger = logging.getLogger(__name__)

class MailMail(models.Model):
    _inherit = 'mail.mail'

    def unlink(self):
        # 🔥 BLOCK deletion of sent mails
        return True

    def create(self, vals_list):
        _logger.error("🔥 MAIL CREATE TRIGGERED: %s", vals_list)
        return super().create(vals_list)