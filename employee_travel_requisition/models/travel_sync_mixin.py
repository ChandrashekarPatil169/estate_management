from odoo import models


class TravelSyncMixin(models.AbstractModel):
    _name = 'travel.sync.mixin'
    _description = 'Sync Travel Lines to Advance Lines'

    def _sync_to_advance(self, vals, relation_field):

        # 🛑 prevent infinite loop
        if self.env.context.get('skip_sync'):
            return

        for rec in self:

            advance_lines = self.env['travel.advance.line'].search([
                (relation_field, '=', rec.id)
            ])

            for line in advance_lines:

                update_vals = {}

                # sync price
                if 'unit_price' in vals and hasattr(rec, 'unit_price'):
                    update_vals['unit_price'] = rec.unit_price

                # sync description
                if 'description' in vals and hasattr(rec, 'description'):
                    update_vals['line_description'] = rec.description

                if update_vals:
                    line.with_context(skip_sync=True).write(update_vals)