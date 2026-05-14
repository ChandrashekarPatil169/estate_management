from odoo import models, fields, api


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    resolved_date = fields.Datetime()
    is_approved = fields.Boolean(default=False)
    state = fields.Selection([
        ('new', 'New'),
        ('submitted', 'Submitted'),
        ('assigned', 'Assigned'),
        ('resolved', 'Resolved'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], compute='_compute_state_from_stage', store=True, tracking=True)

    @api.depends('stage_id')
    def _compute_state_from_stage(self):
        for rec in self:

            stage_submitted = self.env.ref('helpdesk_ticket_email.stage_submitted', raise_if_not_found=False)
            stage_assigned = self.env.ref('helpdesk_ticket_email.stage_assigned', raise_if_not_found=False)
            stage_resolved = self.env.ref('department_helpdesk.helpdesk_ticket_stage_resolved',
                                          raise_if_not_found=False)
            stage_done = self.env.ref('helpdesk_mgmt.helpdesk_ticket_stage_done', raise_if_not_found=False)
            stage_cancelled = self.env.ref('helpdesk_mgmt.helpdesk_ticket_stage_cancelled', raise_if_not_found=False)

            if stage_submitted and rec.stage_id == stage_submitted:
                rec.state = 'submitted'

            elif stage_assigned and rec.stage_id == stage_assigned:
                rec.state = 'assigned'

            elif stage_resolved and rec.stage_id == stage_resolved:
                rec.state = 'resolved'

            elif stage_done and rec.stage_id == stage_done:
                rec.state = 'done'

            elif stage_cancelled and rec.stage_id == stage_cancelled:
                rec.state = 'cancelled'

            else:
                rec.state = 'new'

    def action_cancel_ticket(self):
        stage = self.env.ref(
            'helpdesk_mgmt.helpdesk_ticket_stage_cancelled',
            raise_if_not_found=False
        )

        for rec in self:
            if stage:
                rec.stage_id = stage.id

            rec.message_post(body="❌ Ticket Cancelled")

    def action_submit_ticket(self):
        stage = self.env.ref('helpdesk_ticket_email.stage_submitted', raise_if_not_found=False)

        template = self.env.ref(
            'helpdesk_ticket_email.ticket_submit_email_template',
            raise_if_not_found=False
        )

        for rec in self:
            # ✅ Update stage
            if stage:
                rec.stage_id = stage.id

            print("Manager:", rec.manager_id_main.name if rec.manager_id_main else "No Manager")

            if not template:
                print("❌ TEMPLATE NOT FOUND")
                continue

            # ✅ Manager email
            manager_email = rec.manager_id_main.email if rec.manager_id_main else False

            # ✅ Followers emails
            follower_emails = rec.message_partner_ids.mapped('email')
            follower_emails = [email for email in follower_emails if email]

            print("Followers:", follower_emails)

            # ❌ If no emails
            if not manager_email and not follower_emails:
                print("❌ No emails found")
                continue

            # ✅ Combine emails
            emails = []
            if manager_email:
                emails.append(manager_email)

            emails += follower_emails

            # ✅ Remove duplicates
            emails = list(set(emails))

            email_to = ",".join(emails)

            print("📧 Sending to:", email_to)

            # ✅ SEND EMAIL
            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_to': email_to,
                    'email_from': rec.user_id.email or self.env.user.email
                }
            )

            # ✅ Notify followers in chatter
            rec.message_post(
                body=f"📧 Email sent to {email_to}",
                partner_ids=rec.message_partner_ids.ids
            )

            print("✅ EMAIL SENT")

    def action_assign_ticket(self):
        stage = self.env.ref('helpdesk_ticket_email.stage_assigned', raise_if_not_found=False)

        template = self.env.ref(
            'helpdesk_ticket_email.ticket_assign_email_template',
            raise_if_not_found=False
        )

        for rec in self:
            # ✅ Update stage
            if stage:
                rec.stage_id = stage.id

            print("Manager:", rec.manager_id_main.name if rec.manager_id_main else "No Manager")
            print("Assign To:", rec.assign_to.name if rec.assign_to else "No User")

            if not template:
                print("❌ TEMPLATE NOT FOUND")
                continue

            # ✅ Logged-in user (manager)
            current_user_email = self.env.user.email

            # ✅ Assigned person
            assigned_email = rec.assign_to.email if rec.assign_to else False

            # ✅ Followers
            follower_emails = rec.message_partner_ids.mapped('email')
            follower_emails = [email for email in follower_emails if email]

            print("Followers:", follower_emails)

            # ❌ No emails check
            if not current_user_email and not assigned_email and not follower_emails:
                print("❌ No emails found")
                continue

            # ✅ Combine all emails
            emails = []

            if current_user_email:
                emails.append(current_user_email)

            if assigned_email:
                emails.append(assigned_email)

            emails += follower_emails

            # ✅ Remove duplicates
            emails = list(set(emails))

            email_to = ",".join(emails)

            print("📧 Sending to:", email_to)

            # ✅ SEND EMAIL
            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_from': current_user_email,
                    'email_to': email_to
                }
            )

            # ✅ Notify followers
            rec.message_post(
                body=f"📧 Assignment email sent to {email_to}",
                partner_ids=rec.message_partner_ids.ids
            )

            print("✅ ASSIGN EMAIL SENT")

    def action_resolve_ticket(self):
        stage = self.env.ref(
            'department_helpdesk.helpdesk_ticket_stage_resolved',
            raise_if_not_found=False
        )

        template = self.env.ref(
            'helpdesk_ticket_email.ticket_resolve_email_template',
            raise_if_not_found=False
        )

        for rec in self:
            # ✅ Update stage
            if stage:
                rec.stage_id = stage.id

            rec.resolved_date = fields.Datetime.now()

            if not template:
                print("❌ TEMPLATE NOT FOUND")
                continue

            # ✅ Manager
            manager_email = rec.manager_id_main.email if rec.manager_id_main else False

            # ✅ Requested Person (IMPORTANT FIX)
            requested_email = rec.requested_person_id.email if rec.requested_person_id else False

            # ✅ Followers
            follower_emails = rec.message_partner_ids.mapped('email')
            follower_emails = [email for email in follower_emails if email]

            print("Manager:", manager_email)
            print("Requested Person:", requested_email)
            print("Followers:", follower_emails)

            # ❌ If no emails
            if not manager_email and not requested_email and not follower_emails:
                print("❌ No emails found")
                continue

            # ✅ Combine emails
            emails = []

            if manager_email:
                emails.append(manager_email)

            if requested_email:
                emails.append(requested_email)

            emails += follower_emails

            # ✅ Remove duplicates
            emails = list(set(emails))

            email_to = ",".join(emails)

            print("📧 Sending to:", email_to)

            # ✅ SEND EMAIL
            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_to': email_to,
                    'email_from': self.env.user.email
                }
            )

            # ✅ Notify followers
            rec.message_post(
                body=f"📧 Resolve email sent to {email_to}",
                partner_ids=rec.message_partner_ids.ids
            )

            print("✅ RESOLVE EMAIL SENT")

    def action_done_ticket(self):
        stage = self.env.ref(
            'helpdesk_mgmt.helpdesk_ticket_stage_done',
            raise_if_not_found=False
        )

        template = self.env.ref(
            'helpdesk_ticket_email.ticket_done_email_template',
            raise_if_not_found=False
        )

        for rec in self:
            if stage:
                rec.stage_id = stage.id

            manager_email = rec.manager_id_main.email if rec.manager_id_main else False
            requester_email = rec.partner_id.email if rec.partner_id else False

            # ✅ Followers emails (clean)
            follower_emails = rec.message_partner_ids.mapped('email')
            follower_emails = [email for email in follower_emails if email]

            print("Followers:", follower_emails)

            # ✅ Combine all emails
            emails = []
            if manager_email:
                emails.append(manager_email)
            if requester_email:
                emails.append(requester_email)

            emails += follower_emails

            # ✅ Remove duplicates
            emails = list(set(emails))

            if not emails:
                print("❌ No emails found")
                continue

            email_to = ",".join(emails)

            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_to': email_to,
                    'email_from': self.env.user.email
                }
            )

            # ✅ notify followers in chatter
            rec.message_post(
                body=f"📧 Email sent to {email_to}",
                partner_ids=rec.message_partner_ids.ids
            )

            print("✅ EMAIL SENT:", email_to)

    def _cron_send_pending_approval_reminder(self):

        resolved_stage = self.env.ref(
            'department_helpdesk.helpdesk_ticket_stage_resolved',
            raise_if_not_found=False
        )

        done_stage = self.env.ref(
            'helpdesk_mgmt.helpdesk_ticket_stage_done',
            raise_if_not_found=False
        )

        template = self.env.ref(
            'helpdesk_ticket_email.ticket_resolve_email_template',  # or create new template
            raise_if_not_found=False
        )

        if not template:
            return

        # ✅ Find tickets: Resolved but NOT Done
        tickets = self.search([
            ('stage_id', '=', resolved_stage.id),
        ])

        for rec in tickets:

            # ❗ skip if already moved to Done
            if rec.stage_id == done_stage:
                continue

            # ❗ skip if no manager
            if not rec.manager_id_main or not rec.manager_id_main.email:
                continue

            print("⏰ Reminder for ticket:", rec.name)

            template.send_mail(
                rec.id,
                force_send=True,
                email_values={
                    'email_to': rec.manager_id_main.email,
                    'email_from': self.env.user.email
                }
            )

            rec.message_post(
                body=f"⏰ Reminder email sent to manager ({rec.manager_id_main.email})"
            )
