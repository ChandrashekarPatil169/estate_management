from odoo import models, api
from odoo.exceptions import ValidationError

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['auto_delete'] = False
        return super().create(vals_list)