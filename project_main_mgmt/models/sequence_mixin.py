# models/sequence_mixin.py
from odoo import models


class HierarchySequenceMixin(models.AbstractModel):
    _name = 'hierarchy.sequence.mixin'
    _description = 'Hierarchy Sequence Helper'

    def _next_sequence(self, domain):
        # Check if the column actually exists in the database table
        self.env.cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = 'sequence_no'
        """, (self._table,))

        if not self.env.cr.fetchone():
            return 1  # Fallback if column isn't created yet

        domain = list(domain) + [('sequence_no', '!=', False)]
        last = self.search(domain, order="sequence_no desc", limit=1)
        return (last.sequence_no or 0) + 1

# # models/sequence_mixin.py
# from odoo import models
#
# class HierarchySequenceMixin(models.AbstractModel):
#     _name = 'hierarchy.sequence.mixin'
#     _description = 'Hierarchy Sequence Helper'
#
#     def _next_sequence(self, domain):
#         domain = list(domain) + [('sequence_no', '!=', False)]
#
#         last = self.search(domain, order="sequence_no desc", limit=1)
#         return (last.sequence_no or 0) + 1
