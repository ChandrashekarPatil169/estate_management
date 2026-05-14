from odoo import models, _,fields,api
from odoo.exceptions import AccessError


class MailFollowers(models.Model):
    _inherit = 'mail.followers'

    def write(self, vals):
        # 1. 🚀 ALLOW MANAGERS: Add your groups to the bypass list
        is_manager = (
                self.env.user.has_group('base.group_system') or
                self.env.user.has_group('project.group_project_manager') or
                self.env.user.has_group('project_main_mgmt.group_program_manager') or
                self.env.user.has_group('project_main_mgmt.group_custom_project_manager')
        )

        # If they are a manager, skip all security checks and allow the write
        if is_manager:
            return super().write(vals)

        # 2. KEEP YOUR EXISTING RESTRICTION FOR EVERYONE ELSE
        if 'subtype_ids' in vals:
            restricted_xmlids = [
                # project
                'project_main_mgmt.mt_project_kanban_drag_access',
                'project_main_mgmt.mt_project_governance_access',
                'project_main_mgmt.mt_project_deadline_change_access',
                # ... (keep the rest of your long list here)
            ]

        if not self.env.user.has_group('base.group_system') and 'subtype_ids' in vals:
            restricted_xmlids = [
                # project
                'project_main_mgmt.mt_project_kanban_drag_access',
                'project_main_mgmt.mt_project_governance_access',
                'project_main_mgmt.mt_project_deadline_change_access',


                # backlog
                'project_main_mgmt.mt_project_product_backlog_kanban_drag_access',
                'project_main_mgmt.mt_project_product_backlog_governance_access',
                'project_main_mgmt.mt_project_product_backlog_deadline_access',


                # epic
                'project_main_mgmt.mt_project_epic_kanban_drag_access',
                'project_main_mgmt.mt_project_epic_governance_access',
                'project_main_mgmt.mt_project_epic_deadline_access',


                # story
                'project_main_mgmt.mt_project_user_story_kanban_drag_access',
                'project_main_mgmt.mt_project_user_story_governance_access',
                'project_main_mgmt.mt_project_user_story_deadline_access',


                # task
                'project_main_mgmt.mt_project_task_kanban_drag_access',
                'project_main_mgmt.mt_project_task_governance_access',
                'project_main_mgmt.mt_project_task_deadline_access',


                # subtask
                'project_main_mgmt.mt_project_subtask_kanban_drag_access',
                'project_main_mgmt.mt_project_subtask_governance_access',
                'project_main_mgmt.mt_project_subtask_deadline_access',

            ]

            restricted_subtypes = self.env['mail.message.subtype']
            for xmlid in restricted_xmlids:
                try:
                    restricted_subtypes |= self.env.ref(xmlid)
                except ValueError:
                    pass

            subtype_ids = set()
            for command in vals.get('subtype_ids', []):
                if isinstance(command, (list, tuple)) and len(command) >= 2:
                    if command[0] == 6:
                        subtype_ids.update(command[2])
                    elif command[0] == 4:
                        subtype_ids.add(command[1])

            if restricted_subtypes and subtype_ids.intersection(set(restricted_subtypes.ids)):
                raise AccessError(_("Only Administrator can assign special project access permissions."))

        return super().write(vals)







class MailMessage(models.Model):
    _inherit = 'mail.message'

    # def _is_project_user_readonly_mode(self):
    #     return (
    #         self.env.user.has_group('project.group_project_user')
    #         and not self.env.user.has_group('base.group_system')
    #     )
    def _is_project_user_readonly_mode(self):
        return (
                self.env.user.has_group('project.group_project_user')
                and not self.env.user.has_group('base.group_system')
                and not self.env.user.has_group('project.group_project_manager')  # native Odoo PM
                and not self.env.user.has_group('project_main_mgmt.group_program_manager')
                and not self.env.user.has_group('project_main_mgmt.group_custom_project_manager')
        )

    def write(self, vals):
        # Admin full access
        if self.env.user.has_group('base.group_system'):
            return super().write(vals)

        # Only restrict Project User
        if self._is_project_user_readonly_mode():
            allowed_fields = {
                'body',
                'attachment_ids',
                'partner_ids',
            }

            technical_ok = {
                'write_date',
                'write_uid',
                '__last_update',
                'display_name',
            }

            forbidden = (set(vals.keys()) - technical_ok) - allowed_fields
            if forbidden:
                raise AccessError(_("Only Log Note text can be edited."))

            for message in self:
                # only own message
                if message.author_id and message.author_id.id != self.env.user.partner_id.id:
                    raise AccessError(_("You can edit only your own Log Note."))

                # block system tracking logs
                if message.tracking_value_ids:
                    raise AccessError(_("System tracking logs cannot be edited."))

                # allow only internal note (Log Note)
                mt_note = self.env.ref('mail.mt_note', raise_if_not_found=False)
                if mt_note and message.subtype_id and message.subtype_id.id != mt_note.id:
                    raise AccessError(_("Only Log Note can be edited. Send Message cannot be edited."))

        return super().write(vals)




class MailActivity(models.Model):
    _inherit = 'mail.activity'

    # def _is_project_user_readonly_mode(self):
    #     return (
    #         self.env.user.has_group('project.group_project_user')
    #         and not self.env.user.has_group('base.group_system')
    #     )
    def _is_project_user_readonly_mode(self):
        return (
                self.env.user.has_group('project.group_project_user')
                and not self.env.user.has_group('base.group_system')
                and not self.env.user.has_group('project.group_project_manager')  # native Odoo PM
                and not self.env.user.has_group('project_main_mgmt.group_program_manager')
                and not self.env.user.has_group('project_main_mgmt.group_custom_project_manager')
        )

    @api.model_create_multi
    def create(self, vals_list):
        if self._is_project_user_readonly_mode():
            raise AccessError(_("Only Administrator can use Activity. Project Users can edit only Log Note."))
        return super().create(vals_list)

    def write(self, vals):
        if self._is_project_user_readonly_mode():
            raise AccessError(_("Only Administrator can edit Activity. Project Users can edit only Log Note."))
        return super().write(vals)

    def unlink(self):

        # ✅ ALLOW SYSTEM / INTERNAL FLOW
        if (
                self.env.context.get('from_timer_create')
                or self.env.context.get('mail_create_nosubscribe')
                or self.env.context.get('tracking_disable')
                or self.env.context.get('skip_activity_check')
        ):
            return super().unlink()

        # ✅ NORMAL SECURITY
        if self._is_project_user_readonly_mode():
            raise AccessError(_("Only Administrator can delete Activity. Project Users can edit only Log Note."))

        return super().unlink()


# from odoo import models, _
# from odoo.exceptions import AccessError
#
#
# class MailFollowers(models.Model):
#     _inherit = 'mail.followers'
#
#     def _get_restricted_project_access_subtypes(self):
#         subtype_xmlids = [
#             'project_main_mgmt.mt_project_kanban_drag_access',
#             'project_main_mgmt.mt_project_governance_access',
#             'project_main_mgmt.mt_project_deadline_change_access',
#         ]
#
#         subtype_ids = []
#         for xmlid in subtype_xmlids:
#             subtype = self.env.ref(xmlid, raise_if_not_found=False)
#             if subtype:
#                 subtype_ids.append(subtype.id)
#
#         return subtype_ids
#
#     def write(self, vals):
#         # Admin can always edit
#         if self.env.user.has_group('base.group_system'):
#             return super().write(vals)
#
#         # Only check when subtype_ids is being changed
#         if 'subtype_ids' in vals:
#             restricted_subtype_ids = self._get_restricted_project_access_subtypes()
#
#             for follower in self:
#                 # Only protect project.project followers
#                 if follower.res_model != 'project.project':
#                     continue
#
#                 current_ids = set(follower.subtype_ids.ids)
#                 new_ids = set(current_ids)
#
#                 commands = vals.get('subtype_ids', [])
#                 for command in commands:
#                     if not isinstance(command, (list, tuple)) or len(command) < 1:
#                         continue
#
#                     cmd = command[0]
#
#                     # (6, 0, ids) => replace all
#                     if cmd == 6:
#                         new_ids = set(command[2] or [])
#
#                     # (4, id) => add
#                     elif cmd == 4:
#                         new_ids.add(command[1])
#
#                     # (3, id) => remove
#                     elif cmd == 3:
#                         new_ids.discard(command[1])
#
#                     # (5,) => clear all
#                     elif cmd == 5:
#                         new_ids.clear()
#
#                 # Check if restricted subtype changed
#                 current_restricted = current_ids.intersection(restricted_subtype_ids)
#                 new_restricted = new_ids.intersection(restricted_subtype_ids)
#
#                 if current_restricted != new_restricted:
#                     raise AccessError(_(
#                         "Only Administrator can change Kanban Drag & Drop Access, Governance Access, or Changing Deadline in follower subscriptions."
#                     ))
#
#         return super().write(vals)