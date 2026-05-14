from odoo import models, fields, api
from odoo.exceptions import AccessError

class EstateHierarchyMixin(models.AbstractModel):
    _name = 'estate.hierarchy.mixin'
    _description = 'Estate Hierarchy Engine'
    _order = "id desc"
    # _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    # --------------------------------------------------
    # INTERNAL: add record to a parent's M2M safely
    # --------------------------------------------------
    def _add_to_parent(self, parent, field_name):
        if parent and field_name in parent._fields:
            parent.write({field_name: [(4, self.id)]})

    # --------------------------------------------------
    # ACTION: open M2M like document smart button
    # --------------------------------------------------
    def _open_hdown(self, title, model, records, context=None):
        self.ensure_one()
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': model,
            'view_mode': 'list,form',
            'domain': [('id', 'in', records.ids)],
            'context': context or {},
        }

    def _open_hup(self, title, model, record):
        self.ensure_one()
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': model,
            'view_mode': 'form',
            'res_id': record.id if record else False,
        }




class EstateSecurityMixin(models.AbstractModel):
    _name = 'estate.security.mixin'
    _description = 'Security Enforcement'

    def check_access_rule(self, operation):
        # 1. RUN DEFAULT ODOO RULES FIRST
        super(EstateSecurityMixin, self).check_access_rule(operation)

        # 2. ONLY CARE ABOUT WRITE/UNLINK
        if operation not in ('write', 'unlink'):
            return True

        user = self.env.user

        # 3. BYPASS ADMIN
        if user._is_system():
            return True

        # 4. ONLY RESTRICT ESTATE USERS
        if not user.has_group('estate_management.group_estate_user'):
            return True

        # DEBUG: Uncomment the line below to check your terminal/logs
        # print(f"DEBUG: Security Check Triggered for {self._name} by {user.name}")

        # 5. SUDO SEARCH (Essential: users usually can't read mail.followers)
        allowed_ids = self.env['mail.followers'].sudo().search([
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('partner_id', '=', user.partner_id.id),
            ('can_edit', '=', True)
        ]).mapped('res_id')

        for record in self:
            is_owner = record.create_uid.id == user.id
            is_allowed = record.id in allowed_ids

            if not (is_owner or is_allowed):
                raise AccessError(_("Permission Denied: can_edit is False or you are not the owner."))

        return True
