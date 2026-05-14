from odoo import models, fields, api


class QCStatusWizard(models.TransientModel):
    _name = 'qc.status.wizard'
    _description = 'QC Status Popup'

    qc_id = fields.Many2one('material.quality.check', readonly=True)


    wizard_requester_id = fields.Many2one(related="qc_id.requester_id")
    wizard_admin_1_id = fields.Many2one(related="qc_id.admin_1_id")
    wizard_admin_2_id = fields.Many2one(related="qc_id.admin_2_id")

    # ⭐ ADD PRODUCT LINES IN POPUP
    wizard_line_ids = fields.One2many(
        related="qc_id.line_ids",
        readonly=True
    )

