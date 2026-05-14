from odoo import models, fields,api,_
from odoo.exceptions import AccessError
from odoo import _

# =========================
# USER HIERARCHY
# =========================

class ResUsers(models.Model):
    _inherit = 'res.users'
    _parent_name = 'parent_id'
    _parent_store = True

    parent_id = fields.Many2one('res.users', string="Manager")
    child_ids = fields.One2many('res.users', 'parent_id', string="Subordinates")
    parent_path = fields.Char(index=True)




class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    can_edit = fields.Boolean("Can Edit")


# =========================
# WIZARD (SET can_edit)
# =========================

class MailFollowersEdit(models.TransientModel):
    _inherit = 'mail.followers.edit'

    can_edit = fields.Boolean("Can Edit")

    show_can_edit = fields.Boolean(compute="_compute_show_can_edit")

    # 🔥 ADD THIS METHOD
    @api.depends('partner_ids')
    def _compute_show_can_edit(self):
        for rec in self:
            rec.show_can_edit = False

            users = self.env['res.users'].search([
                ('partner_id', 'in', rec.partner_ids.ids)
            ])

            # ✅ show only if ANY is estate_user
            if any(user.has_group('estate_management.group_estate_user') for user in users):
                rec.show_can_edit = True

    def edit_followers(self):
        res = super().edit_followers()

        for wizard in self:
            if not wizard.res_ids:
                continue

            if isinstance(wizard.res_ids, str):
                res_ids = [int(x) for x in wizard.res_ids.strip('[]').split(',') if x]
            else:
                res_ids = wizard.res_ids

            followers = self.env['mail.followers'].search([
                ('res_model', '=', wizard.res_model),
                ('res_id', 'in', res_ids),
                ('partner_id', 'in', wizard.partner_ids.ids)
            ])

            for follower in followers:
                follower.sudo().can_edit = wizard.can_edit  # 🔥 FIX

        return res
