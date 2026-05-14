from odoo import models, fields,api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()

        for picking in self:
            if (
                picking.picking_type_id.code == 'incoming'
                and picking.state == 'done'
                and picking.purchase_id
            ):
                po = picking.purchase_id

                incoming_pickings = po.picking_ids.filtered(
                    lambda p: p.picking_type_id.code == 'incoming'
                )

                if incoming_pickings and all(p.state == 'done' for p in incoming_pickings):

                    if po.pr_id:
                        po.pr_id.write({'state': 'received'})

                    if po.state == 'purchase':
                        po.write({'state': 'received'})

        return res

    # def button_validate(self):
    #
    #     res = super().button_validate()
    #     for picking in self:
    #         if (
    #                 picking.picking_type_id.code == 'incoming'
    #                 and picking.state == 'done'
    #                 and picking.purchase_id
    #         ):
    #             po = picking.purchase_id
    #
    #             # keep your requisition logic
    #             if po.pr_id:
    #                 po.pr_id.write({'state': 'received'})
    #
    #             # 🔥 move PO to Received only when fully received
    #             incoming_pickings = po.picking_ids.filtered(
    #                 lambda p: p.picking_type_id.code == 'incoming'
    #             )
    #
    #             if all(p.state == 'done' for p in incoming_pickings):
    #                 if po.state == 'purchase':
    #                     po.write({'state': 'done'})  # ✅ THIS IS THE FIX
    #
    #     return res



