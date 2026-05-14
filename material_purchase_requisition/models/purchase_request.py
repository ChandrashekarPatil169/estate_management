from odoo import models, fields
from odoo.exceptions import UserError

class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'  # adjust if different

    approved_user_ids = fields.Many2many(
        'res.users',
        string='Approved By',
        copy=False,
        tracking=True
    )

    def _get_required_approvers(self):
        self.ensure_one()

        approvers = set()

        # 1️⃣ Department manager (EXISTING LOGIC – KEEP)
        if not self.department_id.manager_id.user_id:
            raise UserError("Department manager user is not configured.")

        approvers.add(self.department_id.manager_id.user_id)

        # 2️⃣ Amount-based approvers (NEW)
        matrix = self.env['purchase.approval.matrix'].search([
            ('min_amount', '<=', self.amount_total),
            ('max_amount', '>=', self.amount_total),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not matrix:
            raise UserError("No approval matrix configured for this amount.")

        approvers |= set(matrix.approver_ids)

        return approvers
