from odoo import models, fields

class QCRejectionWizard(models.TransientModel):
    _name = 'qc.rejection.wizard'
    _description = 'Quality Check Rejection Wizard'

    qc_id = fields.Many2one('material.quality.check', required=True)
    reason = fields.Text(string="Reason for Rejection", required=True)

    def action_confirm_rejection(self):
        # Use .sudo() to ensure the write is permitted
        qc = self.qc_id.sudo()

        qc.write({
            'rejection_reason': self.reason,
        })

        # Set the specific checker's status to 'fail'
        if self.env.user == qc.requester_id:
            qc.req_status = 'fail'
        elif self.env.user == qc.admin_1_id:
            qc.adm1_status = 'fail'
        elif self.env.user == qc.admin_2_id:
            qc.adm2_status = 'fail'
        else:
            # Fallback if an admin who isn't an assigned checker tries to reject
            qc.adm1_status = 'fail'
