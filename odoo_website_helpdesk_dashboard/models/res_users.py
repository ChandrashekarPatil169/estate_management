from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    show_helpdesk_dashboard = fields.Boolean(
        string="Show Helpdesk Dashboard",
        default=False
    )

    def write(self, vals):
        res = super().write(vals)

        if 'show_helpdesk_dashboard' in vals:
            group = self.env.ref(
                'department_helpdesk.group_helpdesk_dashboard_access'
            )

            for user in self:
                if user.show_helpdesk_dashboard:
                    user.groups_id = [(4, group.id)]
                else:
                    user.groups_id = [(3, group.id)]

        return res