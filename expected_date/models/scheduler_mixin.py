from datetime import timedelta
from odoo import models, fields, api


class SchedulerMixin(models.AbstractModel):
    _name = 'scheduler.mixin'
    _description = 'Generic Forward Scheduling Engine'

    planned_start_date = fields.Date(string="Planned Start Date", tracking=True)
    planned_end_date = fields.Date(string="Planned End Date", tracking=True)
    expected_end_date = fields.Date(string="Expected End Date", tracking=True)
    completed_date = fields.Datetime(string="Completed Date", tracking=True)
    sequence_no = fields.Integer(index=True)

    # ==========================================================
    # WRITE OVERRIDE
    # ==========================================================
    # def write(self, vals):
    #     # # 🔹 Auto-set expected_end_date when planned_end_date is updated
    #     # if 'planned_end_date' in vals and vals.get('planned_end_date'):
    #     #     planned_end_date = fields.Date.to_date(vals.get('planned_end_date'))
    #     #     vals['expected_end_date'] = planned_end_date + timedelta(days=1)
    #
    #     res = super().write(vals)
    #
    #
    #     # trigger_fields = ['planned_end_date', 'completed_date']
    #     trigger_fields = [
    #         'planned_start_date',
    #         'planned_end_date',
    #         'completed_date'
    #     ]
    #
    #     if any(field in vals for field in trigger_fields):
    #         for record in self:
    #             record._forward_chain()
    #
    #     return res
    def write(self, vals):
        res = super().write(vals)

        # Skip chain during cron/manual controlled updates
        if self.env.context.get('skip_scheduler_chain'):
            return res

        trigger_fields = [
            'planned_start_date',
            'planned_end_date',
            'completed_date'
        ]
        ############### disabled forward chain
        if any(field in vals for field in trigger_fields):
            for record in self:
                record._forward_chain()

        return res
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)



        for rec in records:
            if rec.planned_end_date or rec.completed_date:
                rec._forward_chain()

        return records

    @api.onchange('planned_start_date', 'planned_end_date', 'completed_date')
    def _onchange_expected_date(self):
        for rec in self:
            if rec.completed_date:
                rec.expected_end_date = rec.completed_date.date() if hasattr(rec.completed_date,
                                                                             'date') else rec.completed_date
            elif rec.planned_end_date:
                rec.expected_end_date = rec.planned_end_date + timedelta(days=1)

    # ==========================================================
    # FORWARD CHAIN LOGIC
    # ==========================================================
    def _forward_chain(self):
        for record in self:

            # Always calculate fresh from current values
            if record.completed_date:
                expected = record.completed_date.date() if hasattr(record.completed_date,
                                                                   'date') else record.completed_date
            elif record.planned_end_date:
                expected = record.planned_end_date + timedelta(days=1)
            else:
                continue

            # super(SchedulerMixin, record).write({
            #     'expected_end_date': expected
            # })
            record.with_context(
                skip_scheduler_chain=True,
                skip_deadline_access_check=True,
                skip_project_readonly_check=True,
                allow_governance_write=True,
                from_kanban_drag_auto=True,
            ).sudo().write({
                'expected_end_date': expected
            })

            previous_expected = expected

            parent_field = record._get_parent_field()
            if not parent_field:
                continue

            parent = getattr(record, parent_field)
            if not parent:
                continue

            # siblings = record.search(
            #     [
            #         (parent_field, '=', parent.id),
            #         ('sequence_no', '>', record.sequence_no)
            #     ],
            #     order="sequence_no asc"
            # )
            #
            # for sibling in siblings:
            #     if not sibling.planned_start_date or not sibling.planned_end_date:
            #         break
            #
            #     duration = (sibling.planned_end_date - sibling.planned_start_date).days
            #
            #     new_start = previous_expected
            #     new_end = new_start + timedelta(days=duration)
            #
            #     if sibling.completed_date:
            #         new_expected = sibling.completed_date.date() if hasattr(sibling.completed_date,
            #                                                                 'date') else sibling.completed_date
            #     else:
            #         new_expected = new_end + timedelta(days=1)
            #
            #     # super(SchedulerMixin, sibling).write({
            #     #     'planned_start_date': new_start,
            #     #     'planned_end_date': new_end,
            #     #     'expected_end_date': new_expected,
            #     # })
            #     sibling.with_context(
            #         skip_scheduler_chain=True,
            #         skip_deadline_access_check=True,
            #         skip_project_readonly_check=True,
            #         allow_governance_write=True,
            #         from_kanban_drag_auto=True,
            #     ).sudo().write({
            #         'planned_start_date': new_start,
            #         'planned_end_date': new_end,
            #         'expected_end_date': new_expected,
            #     })
            #
            #     previous_expected = new_expected

            record._rollup_parent()

    # def _rollup_parent(self):
    #     for record in self:
    #         parent_field = record._get_parent_field()
    #         if not parent_field:
    #             continue
    #
    #         parent = getattr(record, parent_field, False)
    #         if not parent:
    #             continue
    #
    #         # 🔥 STOP here if parent is project.project
    #         if parent._name == 'project.project':
    #             continue
    #
    #         children = record.search(
    #             [(parent_field, '=', parent.id)],
    #             order="sequence_no asc, id asc"
    #         )
    #
    #         if not children:
    #             continue
    #
    #         last_child = children[-1]
    #         vals = {}
    #
    #         if last_child.completed_date:
    #             completed_date = (
    #                 last_child.completed_date.date()
    #                 if hasattr(last_child.completed_date, 'date')
    #                 else last_child.completed_date
    #             )
    #             vals['expected_end_date'] = completed_date
    #         elif last_child.expected_end_date:
    #             vals['expected_end_date'] = last_child.expected_end_date
    #         elif last_child.planned_end_date:
    #             vals['expected_end_date'] = last_child.planned_end_date + timedelta(days=1)
    #
    #         if vals:
    #             parent.with_context(
    #                 skip_scheduler_chain=True,
    #                 skip_deadline_access_check=True,
    #                 skip_project_readonly_check=True,
    #                 allow_governance_write=True,
    #                 from_kanban_drag_auto=True,
    #             ).sudo().write(vals)
    #
    #         # continue upward only if parent is not project.project
    #         if hasattr(parent, '_rollup_parent'):
    #             parent._rollup_parent()
    #
    # def

    def _rollup_parent(self):
        for record in self:
            parent_field = record._get_parent_field()
            if not parent_field:
                continue

            parent = getattr(record, parent_field, False)
            if not parent:
                continue

            child_date = record.expected_end_date
            parent_date = parent.expected_end_date

            # 🔥 CORE RULE: only propagate delay
            if child_date and (
                    not parent_date or child_date > parent_date
            ):
                parent.with_context(
                    skip_scheduler_chain=True,
                    skip_deadline_access_check=True,
                    skip_project_readonly_check=True,
                    allow_governance_write=True,
                    from_kanban_drag_auto=True,
                ).sudo().write({
                    'expected_end_date': child_date
                })

                # 🔥 propagate upward ONLY if changed
                if hasattr(parent, '_rollup_parent'):
                    parent._rollup_parent()





    def _get_parent_field(self):
        return False



