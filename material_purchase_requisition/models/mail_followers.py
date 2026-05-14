from odoo import models, fields,api,_
class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    # def create(self, vals):
    #     rec = super().create(vals)
    #
    #     if rec.res_model == 'material.purchase.requisition':
    #         pr = self.env[rec.res_model].browse(rec.res_id)
    #
    #         if pr.employee_id:
    #             users = rec.partner_id.user_ids
    #             for user in users:
    #                 pr.employee_id.visible_to_user_ids = [(4, user.id)]
    #
    #     return rec

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.res_model == 'material.purchase.requisition':
                pr = self.env[rec.res_model].browse(rec.res_id)

                if pr.employee_id and rec.partner_id:
                    users = rec.partner_id.user_ids
                    for user in users:
                        pr.employee_id.visible_to_user_ids = [(4, user.id)]

        return records

from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    visible_to_user_ids = fields.Many2many(
        'res.users',
        string="Visible To Users"
    )