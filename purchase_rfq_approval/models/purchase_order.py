# from pip._internal.utils._jaraco_text import _
from odoo import models, fields,api,_
from odoo.exceptions import UserError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    approval_team_id = fields.Many2one(
        "purchase.approval.team",
        string="Approval Team",tracking=True
    )

    technical_team_id = fields.Many2one(
        'technical.approval.status',  # MASTER MODEL
        string="Technical Team Approval",
        required=False)

    approval_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("to_approve", "Waiting Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True
    )

    approval_history_ids = fields.One2many(
        "purchase.approval.history",
        "order_id",
        string="Approval History",tracking=True
    )

    pr_id = fields.Many2one(
        "material.purchase.requisition",
        string="Purchase Requisition",
        readonly=True,
        index=True,
        ondelete="set null",tracking=True
    )


    vendor_decision = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Vendor Decision",tracking=True)
    vendor_decision_date = fields.Date(string="Vendor Decision Date",tracking=True)
    vendor_reject_reason = fields.Text(string="Vendor Reject Reason",tracking=True)

    is_pr_based = fields.Boolean(
        compute="_compute_is_pr_based",
        store=True,tracking=True
    )
    po_last_reminder_date = fields.Date(string="PO Approval Reminder Date")

    def _compute_is_pr_based(self):
        for order in self:
            order.is_pr_based = bool(order.pr_id)

    def action_submit_for_approval(self):

        for order in self:

            if not order.pr_id:
                raise UserError("Approval only for PR RFQs.")

            if not order.approval_team_id:
                raise UserError("Please select Approval Team.")

            order.approval_state = "to_approve"

            # Create approval history
            self.env["purchase.approval.history"].sudo().create({
                "order_id": order.id,
                "user_id": self.env.user.id,
                "action": "submitted",
            })

            # Load mail template
            template = self.env.ref(
                "purchase_rfq_approval.mail_template_po_submit_approval",
                raise_if_not_found=False
            )

            if not template:
                _logger.warning("Mail template not found!")
                return

            # Get approvers with email
            approvers = order.approval_team_id.rule_ids.mapped(
                "approver_ids"
            ).filtered(lambda u: u.email)

            if not approvers:
                _logger.warning("No approvers with email found.")
                return

            # Combine emails
            email_to = ",".join(approvers.mapped("email"))

            # Send mail
            template.sudo().send_mail(
                order.id,
                force_send=True,
                email_values={
                    "email_to": email_to
                }
            )


    def action_approve(self):
        for order in self:

            # 🔥 ADMIN FULL APPROVAL (ADD HERE)
            if self.env.user.has_group('base.group_system'):
                self.env["purchase.approval.history"].sudo().create({
                    "order_id": order.id,
                    "user_id": self.env.user.id,
                    "action": "approved",
                })

                order.approval_state = "approved"

                continue  # ⭐ VERY IMPORTANT
            rules = order.approval_team_id.rule_ids.filtered(
                    lambda r: r.min_amount <= order.amount_total <= r.max_amount
                )

            if not rules or self.env.user not in rules.approver_ids:
                    raise UserError("You are not authorized to approve this RFQ.")

            self.env["purchase.approval.history"].sudo().create({
                "order_id": order.id,
                "user_id": self.env.user.id,
                "action": "approved",
            })

            order.approval_state = "approved"

    def button_confirm(self):
        for order in self:
            if order.pr_id and not self.env.user.has_group('base.group_system'):
                if order.approval_state != "approved":
                    raise UserError("RFQ must be approved before confirmation.")

                if order.vendor_decision != "yes":
                    raise UserError("Vendor has not accepted the RFQ.")

        # ✅ DO NOT change existing behavior
        res = super().button_confirm()

        # ✅ ADD ONLY THIS (post-confirm hook)
        self._notify_pr_followers_on_po()

        return res

    @api.model
    def create(self, vals):
        order = super().create(vals)
        if not order.pr_id:
            order.approval_state = "approved"
        return order

    def action_reject(self):
        for order in self:
            rules = order.approval_team_id.rule_ids.filtered(
                lambda r: r.min_amount <= order.amount_total <= r.max_amount
            )

            if not rules or self.env.user not in rules.approver_ids:
                raise UserError("You are not authorized to reject this RFQ.")

            self.env["purchase.approval.history"].sudo().create({
                "order_id": order.id,
                "user_id": self.env.user.id,
                "action": "rejected",
            })

            order.approval_state = "rejected"

# ✅ ACCEPT (same as portal accept)
    def action_vendor_accept(self):
        for order in self:

            if order.state not in ['sent', 'vendor_pending']:
                return

            order.write({
                'vendor_decision': 'yes',
                'vendor_decision_date': fields.Date.today(),
            })

            order.message_post(
                body=_("Vendor accepted this RFQ via backend.")
            )

    # ✅ REJECT (same as portal reject)
    def action_vendor_reject(self, reason=None):
        for order in self:

            if order.state not in ['sent', 'vendor_pending']:
                return

            reason = str(reason) if reason else ""

            order.write({
                'vendor_decision': 'no',
                'vendor_decision_date': fields.Date.today(),
                'vendor_reject_reason': reason,
            })

            order.message_post(
                body=f"Vendor rejected this RFQ. Reason: {reason}"
            )

    def action_open_vendor_reject_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject RFQ',
            'res_model': 'purchase.vendor.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    last_vendor_reminder_date = fields.Date(string="Last Vendor Reminder")

    @api.model
    def _cron_vendor_rfq_reminder(self):
        today = fields.Date.today()
        gap_date = today - timedelta(days=1)

        orders = self.search([
            ('state', '=', 'sent'),
            ('vendor_decision', '=', False),
            ('partner_id.email', '!=', False),
            '|',
            ('last_vendor_reminder_date', '=', False),
            ('last_vendor_reminder_date', '<=', gap_date),
        ])

        template = self.env.ref(
            'purchase_rfq_approval.mail_template_vendor_rfq_reminder',
            raise_if_not_found=False
        )

        if not template:
            _logger.error("RFQ Reminder template not found")
            return

        for order in orders:
            partner = order.partner_id

            if not partner or not partner.email:
                _logger.warning("Skipping RFQ %s: no vendor email", order.name)
                continue

            try:
                template.send_mail(order.id)  # queue-based

                order.write({
                    'last_vendor_reminder_date': today
                })

                if order.pr_id:
                    order.pr_id.message_post(
                        body=f"📧 Reminder sent to vendor <b>{partner.name}</b> for RFQ <b>{order.name}</b>",
                        subtype_xmlid="mail.mt_comment"
                    )

            except Exception as e:
                _logger.error("Failed sending reminder for %s: %s", order.name, str(e))

    def _notify_pr_followers_on_po(self):
        template = self.env.ref(
            'purchase_rfq_approval.mail_template_pr_po_confirm',
            raise_if_not_found=False
        )

        if not template:
            for order in self:
                if order.pr_id:
                    order.pr_id.message_post(body="⚠️ Template not found")
            return

        for order in self:
            pr = order.pr_id
            if not pr:
                continue

            # ✅ SAME AS YOUR WORKING LOGIC → ensure requester is follower
            if pr.employee_id.user_id and pr.employee_id.user_id.partner_id:
                pr.message_subscribe(
                    partner_ids=[pr.employee_id.user_id.partner_id.id]
                )

            # ✅ get followers
            partners = pr.message_partner_ids.filtered(lambda p: p.email)

            if not partners:
                pr.message_post(body="⚠️ No followers with email")
                continue

            # ✅ EXACT SAME CALL (no extra tricks)
            pr.message_post_with_source(
                template,
                subtype_xmlid="mail.mt_comment",
                partner_ids=partners.ids
            )

    def _notify_pr_and_approvers_on_submit(self):
        template = self.env.ref(
            'purchase_rfq_approval.mail_template_po_submit_approval',
            raise_if_not_found=False
        )

        if not template:
            for order in self:
                if order.pr_id:
                    order.pr_id.message_post(body="⚠️ Template not found")
            return

        for order in self:
            pr = order.pr_id
            if not pr:
                continue

            # --------------------------------------------------
            # ✅ Ensure requester is follower (same as your working logic)
            # --------------------------------------------------
            if pr.employee_id.user_id and pr.employee_id.user_id.partner_id:
                pr.message_subscribe(
                    partner_ids=[pr.employee_id.user_id.partner_id.id]
                )

            # --------------------------------------------------
            # ✅ PR followers
            # --------------------------------------------------
            pr_partners = pr.message_partner_ids.filtered(lambda p: p.email)

            # --------------------------------------------------
            # ✅ Approval team users
            # --------------------------------------------------
            approvers = order.approval_team_id.rule_ids.mapped(
                "approver_ids"
            ).filtered(lambda u: u.email)

            approver_partners = approvers.mapped("partner_id")

            # --------------------------------------------------
            # ✅ Merge + remove duplicates
            # --------------------------------------------------
            partners = (pr_partners | approver_partners).filtered(lambda p: p.email)

            if not partners:
                pr.message_post(body="⚠️ No followers with email")
                continue

            # --------------------------------------------------
            # ✅ SAME PATTERN AS YOUR WORKING METHOD
            # --------------------------------------------------
            pr.message_post_with_source(
                template,
                subtype_xmlid="mail.mt_comment",
                partner_ids=partners.ids,
                email_layout_xmlid="mail.mail_notification_layout"
            )

    @api.model
    def _cron_po_approval_reminder(self):
        _logger.info("🚀 STARTING PO Approval Reminder Cron")
        today = fields.Date.context_today(self)

        # 1. Search for POs in 'Waiting Approval' state
        # Removed the date check temporarily for your testing
        pending_pos = self.search([
            ('approval_state', '=', 'to_approve'),
            ('approval_team_id', '!=', False)
        ])

        _logger.info("🔍 Found %s POs in 'to_approve' state", len(pending_pos))

        template = self.env.ref('purchase_rfq_approval.mail_template_po_pending_reminder', raise_if_not_found=False)
        if not template:
            _logger.error("❌ Template 'purchase_rfq_approval.mail_template_po_pending_reminder' not found!")
            return

        for po in pending_pos:
            _logger.info("Checking PO: %s (Total: %s)", po.name, po.amount_total)

            # 2. Find the specific rule that matches this PO's amount
            rule = po.approval_team_id.rule_ids.filtered(
                lambda r: r.min_amount <= po.amount_total <= r.max_amount
            )

            if not rule:
                _logger.warning("⚠️ No matching amount rule found for PO %s", po.name)
                continue

            # 3. Get the approvers from that rule
            approvers = rule.mapped('approver_ids').filtered(lambda u: u.email)

            if not approvers:
                _logger.warning("⚠️ No approvers with emails found for PO %s", po.name)
                continue

            email_to = ",".join(approvers.mapped("email"))
            approver_names = ", ".join(approvers.mapped("name"))

            _logger.info("📧 Sending reminder for %s to: %s", po.name, email_to)

            # 4. Post to chatter and send email
            # ✅ Convert approvers → partners
            partner_ids = approvers.mapped("partner_id").ids

            po.with_context(
                approver_name=approver_names,
            ).message_post_with_source(
                template,
                subtype_xmlid='mail.mt_note',
                partner_ids=partner_ids,  # 🔥 CRITICAL FIX
            )

            # 5. Mark as reminded today
            po.po_last_reminder_date = today

        _logger.info("✅ FINISHED PO Approval Reminder Cron")


class PurchaseVendorRejectWizard(models.TransientModel):
    _name = 'purchase.vendor.reject.wizard'

    reason = fields.Text(required=True)

    def action_confirm_reject(self):
        order = self.env['purchase.order'].browse(self.env.context.get('active_id'))
        order.action_vendor_reject(self.reason)



class TechnicalApprovalStatus(models.Model):
    _name = 'technical.approval.status'
    _description = 'Technical Approval Status'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)