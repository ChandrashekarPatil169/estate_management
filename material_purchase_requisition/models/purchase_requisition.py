from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)



class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Material Purchase Requisition"
    _order = "create_date desc"

    name = fields.Char(default="New", readonly=True, copy=False,string="Reference")
    employee_id = fields.Many2one("hr.employee", required=True,string="Employee Name",)
    department_id = fields.Many2one("hr.department", required=True,)
    requisition_owner_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True,
    )
    request_date = fields.Date(default=fields.Date.context_today,)
    reason_for_requisition = fields.Text()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('po_confirmed', 'PO Confirmed'),  # ← ADD THIS LINE
        ('received', 'Received'),
        ('rejected', 'Rejected'),
    ],
        default="draft",
        tracking=True,
        group_expand="_expand_states",
    )


    @api.model
    def _expand_states(self, *args):
        return [key for key, label in self._fields['state'].selection]



    line_ids = fields.One2many(
        "material.purchase.requisition.line",
        "requisition_id",
        
    )

    total_amount = fields.Monetary(
        compute="_compute_total_amount", store=True,
    )

    approval_route = fields.Json(readonly=True,)
    approval_step = fields.Integer(default=0,)
    current_approver_id = fields.Many2one("res.users",)
    purchase_order_ids = fields.One2many(
        "purchase.order",
        "pr_id",
        string="RFQs",
        
    )
    approval_log_ids = fields.One2many(
        'material.purchase.approval.log',
        'requisition_id',
        string='Approval Logs',
    )
    rfq_created = fields.Boolean(
        string="RFQ Created",
        default=False,
        copy=False,
    )

    ##############
    required_date = fields.Date(
        string="Required By Date",

    )
    budget_code = fields.Char(
        string="Budget Code",

    )

    cost_center_id = fields.Many2one(
        'hr.department',
        string="Cost Center / Budget Owner",

    )
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'material.purchase.requisition')],
        string='Supporting Documents',
    )

    attachment_count = fields.Integer(
        compute="_compute_attachment_count",
        string="Attachment Count",
    )
    approval_level = fields.Integer(
        string="Approval Level",
        default=0,

    )

    final_po_id = fields.Many2one(
        'purchase.order',
        string="Final Purchase Order",
        readonly=True,
        
    )

    # submitted_date = fields.Datetime(
    #     string="Submitted On",
    #     readonly=True,
    #     ,
    # )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        tracking=True
    )

    def _compute_attachment_count(self):
        Attachment = self.env['ir.attachment']
        for rec in self:
            rec.attachment_count = Attachment.search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id),
            ])

    submitted_on = fields.Datetime(string="Submitted On",)
    last_reminder_sent_on = fields.Datetime()

    ################

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)],
            limit=1
        )
        if employee:
            res['employee_id'] = employee.id
            res['department_id'] = employee.department_id.id
        return res

    @api.depends("line_ids.quantity", "line_ids.price_unit")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = sum(
                l.quantity * l.price_unit for l in rec.line_ids
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "material.purchase.requisition"
                ) or "New"
        return super().create(vals_list)

    # ---------- M1 → M2 ----------
    def action_submit(self):
        for rec in self:
            # 1️⃣ Line validation
            if not rec.line_ids:
                raise UserError("At least one requisition line is required.")

            # 2️⃣ Amount validation
            if rec.total_amount <= 0:
                raise UserError("Total amount must be greater than zero.")




            # if not rec.cost_center_id:
            #     raise UserError("Cost Center is mandatory.")



            # 5️⃣ Approval route
            route = rec._compute_approval_route()
            if not route:
                raise UserError("Approval route is empty.")

                # 6️⃣ Move to approval
            rec.write({
                "approval_route": route,
                "approval_step": 0,
                "current_approver_id": route[0],
                "state": "pending",
                "submitted_on": fields.Datetime.now(),
                "last_reminder_sent_on": False,
            })

            # ✅ Subscribe requester
            if rec.employee_id.user_id:
                rec.message_subscribe(
                    partner_ids=[rec.employee_id.user_id.partner_id.id]
                )

            # ✅ Notify followers using template
            rec._notify_followers_on_submit()

            rec._notify_current_approver()



        return True



    def _get_user_from_group(self, xml_id):
        group = self.env.ref(xml_id)
        user = self.env['res.users'].search(
            [('groups_id', 'in', group.id), ('active', '=', True)],
            limit=1
        )
        if not user:
            raise UserError(f"No user configured for group {group.display_name}")
        return user

    # ---------- APPROVAL POLICY ----------

    def _compute_approval_route(self):
        self.ensure_one()

        route = []

        # 1️⃣ Department Manager (always automatic)
        dept_manager = self.department_id.manager_id.user_id
        if not dept_manager:
            raise UserError("Department manager user not configured.")

        route.append(dept_manager.id)

        # 2️⃣ Approval Matrix lookup (configuration-driven)
        matrix = self.env['purchase.approval.matrix'].search([
            ('min_amount', '<=', self.total_amount),
            ('max_amount', '>=', self.total_amount),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not matrix:
            raise UserError("No approval configuration found for this amount.")

        # 3️⃣ Add configured approvers (NO hardcoding, NO groups)
        for user in matrix.approver_ids:
            if user.id not in route:  # ✅ de-duplication
                route.append(user.id)

        return route

    is_admin = fields.Boolean(compute="_compute_is_admin")

    def _compute_is_admin(self):
        for rec in self:
            rec.is_admin = self.env.user.has_group('base.group_system')

    # ---------- APPROVE ----------

    # def action_approve(self):
    #     for rec in self:
    #         # if rec.current_approver_id.id != self.env.user.id:
    #         #     raise AccessError("Not authorized.")
    #         # 🔥 ADMIN BYPASS
    #         # 🟢 ADMIN DIRECT APPROVE (ANYTIME)
    #         # ---------------- ADMIN DIRECT APPROVE ----------------
    #         self.env["material.purchase.approval.log"].create({
    #             "requisition_id": rec.id,
    #             "user_id": self.env.user.id,
    #             "action": "approved",  # ✅ correct value
    #         })
    #
    #         rec.write({
    #                 "state": "approved",
    #                 "approval_step": len(rec.approval_route or []),
    #                 "current_approver_id": False,
    #         })
    #
    #         self.env["material.purchase.approval.log"].create({
    #             "requisition_id": rec.id,
    #             "user_id": self.env.user.id,
    #             "action": "approved",
    #             })
    #         # ⭐ ADMIN DIRECT FULL APPROVAL (ADD HERE)
    #         if self.env.user.has_group('base.group_system'):
    #             rec.write({
    #                 "state": "approved",
    #                 "approval_step": len(rec.approval_route),
    #                 "current_approver_id": False,
    #             })
    #
    #             mails = self.env['mail.mail'].sudo().search([
    #                 ('model', '=', 'material.purchase.requisition'),
    #                 ('res_id', '=', rec.id),
    #                 ('state', 'in', ['outgoing', 'exception']),
    #             ])
    #             mails.unlink()
    #
    #             continue
    #
    #         step = rec.approval_step + 1
    #
    #         if step >= len(rec.approval_route):
    #             rec.write({
    #                 "state": "approved",
    #                 "approval_step": step,
    #                 "current_approver_id": False,
    #             })
    #             # 🔥 ADD ONLY THIS BLOCK (DO NOT TOUCH ANYTHING ELSE)
    #             mails = self.env['mail.mail'].sudo().search([
    #                 ('model', '=', 'material.purchase.requisition'),
    #                 ('res_id', '=', rec.id),
    #                 ('state', 'in', ['outgoing', 'exception']),
    #             ])
    #             mails.unlink()
    #         else:
    #             rec.write({
    #                 "approval_step": step,
    #                 "current_approver_id": rec.approval_route[step],
    #                 "last_reminder_sent_on": False,
    #             })
    #
    #             rec._notify_current_approver()
    def action_approve(self):
        for rec in self:

            # ================= ADMIN DIRECT APPROVE =================
            if self.env.user.has_group('base.group_system'):
                rec.write({
                    "state": "approved",
                    "approval_step": len(rec.approval_route or []),
                    "current_approver_id": False,
                })

                self.env["material.purchase.approval.log"].create({
                    "requisition_id": rec.id,
                    "user_id": self.env.user.id,
                    "action": "approved",
                })

                # remove pending mails
                mails = self.env['mail.mail'].sudo().search([
                    ('model', '=', 'material.purchase.requisition'),
                    ('res_id', '=', rec.id),
                    ('state', 'in', ['outgoing', 'exception']),
                ])
                mails.unlink()
                continue

            # ================= NORMAL APPROVER =================
            if rec.current_approver_id.id != self.env.user.id:
                raise AccessError("Not authorized to approve.")

            self.env["material.purchase.approval.log"].create({
                "requisition_id": rec.id,
                "user_id": self.env.user.id,
                "action": "approved",
            })

            step = rec.approval_step + 1

            if step >= len(rec.approval_route):
                rec.write({
                    "state": "approved",
                    "approval_step": step,
                    "current_approver_id": False,
                })

                mails = self.env['mail.mail'].sudo().search([
                    ('model', '=', 'material.purchase.requisition'),
                    ('res_id', '=', rec.id),
                    ('state', 'in', ['outgoing', 'exception']),
                ])
                mails.unlink()

            else:
                rec.write({
                    "approval_step": step,
                    "current_approver_id": rec.approval_route[step],
                    "last_reminder_sent_on": False,
                })
                rec._notify_current_approver()


    # ---------- REJECT ----------
    # def action_reject(self, reason=None):
    #     for rec in self:
    #         # if rec.current_approver_id != self.env.user:
    #         #     raise AccessError("You are not authorized to reject.")
    #         if not self.env.user.has_group('base.group_system'):
    #             if rec.current_approver_id != self.env.user:
    #                 raise AccessError("You are not authorized to reject.")
    #
    #         rec.write({
    #             "state": "rejected",
    #             "rejection_reason": reason or "Rejected",
    #             "current_approver_id": False,
    #         })
    #
    #         self.env["material.purchase.approval.log"].create({
    #             "requisition_id": rec.id,
    #             "user_id": self.env.user.id,
    #             "action": "rejected",
    #             "reason": reason,
    #         })
    #
    #         rec.message_post(
    #             body=f"Rejected by {self.env.user.name}<br/>Reason: {reason or 'Not specified'}"
    #         )
    def action_reject(self, reason=None):
        for rec in self:

            # ADMIN CAN REJECT ANYTIME
            if not self.env.user.has_group('base.group_system'):
                if rec.current_approver_id.id != self.env.user.id:
                    raise AccessError("You are not authorized to reject.")

            rec.write({
                "state": "rejected",
                "rejection_reason": reason or "Rejected",
                "current_approver_id": False,
            })

            self.env["material.purchase.approval.log"].create({
                "requisition_id": rec.id,
                "user_id": self.env.user.id,
                "action": "rejected",
                "reason": reason or "Rejected",
            })

            rec.message_post(
                body=f"❌ Rejected by {self.env.user.name} Reason: {reason or 'Not specified'}"
            )

    def action_create_rfq(self):
        self.ensure_one()

        # # 🔒 HARD GUARD (DO NOT REMOVE)
        # if self.state != "approved":
        #     raise UserError("PR must be approved before creating RFQ.")
        if self.state != "approved" and not self.env.user.has_group('base.group_system'):
            raise UserError("PR must be approved before creating RFQ.")

        return {
            "type": "ir.actions.act_window",
            "name": "Select Vendors",
            "res_model": "material.pr.rfq.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_pr_id": self.id,
            },
        }

        # --------------------------------------------------
        # REMINDER CONFIG FETCH
        # --------------------------------------------------

    def _get_reminder_config(self):
        return self.env['pr.approval.reminder.config'].search(
            [('active', '=', True)],
            order='id desc',
            limit=1
        )

    @api.constrains('active')
    def _check_single_active(self):
        for rec in self:
            if rec.active:
                others = self.search([
                    ('active', '=', True),
                    ('id', '!=', rec.id)
                ])
                if others:
                    raise UserError(
                        "Only one Approval Reminder configuration can be active."
                    )


    # --------------------------------------------------
    # CRON METHOD
    # --------------------------------------------------

    def cron_notify_pending_approvals(self):

        today = fields.Date.today()

        prs = self.search([
            ('state', '=', 'pending'),
            ('current_approver_id', '!=', False),
            ('submitted_on', '!=', False),
        ])

        template = self.env.ref(
            'material_purchase_requisition.mail_template_pr_pending_reminder',
            raise_if_not_found=False
        )

        if not template:
            _logger.error("Reminder template not found")
            return

        for pr in prs:

            # safety
            if pr.state != 'pending' or not pr.current_approver_id:
                continue

            approver = pr.current_approver_id
            email = approver.email or approver.partner_id.email

            if not email:
                pr.message_post(
                    body=f"⚠️ No email for approver {approver.name}"
                )
                continue

            # 🔥 DAILY CONTROL
            last_date = (
                pr.last_reminder_sent_on.date()
                if pr.last_reminder_sent_on else None
            )

            if last_date == today:
                continue  # already sent today

            try:
                _logger.info(f"Daily reminder for PR {pr.name}")

                template.with_context(
                    approver_name=approver.name
                ).sudo().send_mail(
                    pr.id,
                    force_send=True,
                    email_values={
                        'email_to': email,
                    }
                )

                # 🔥 update timestamp
                pr.last_reminder_sent_on = fields.Datetime.now()

                # 🔥 chatter log
                pr.message_post(
                    body=f"⏰ Reminder sent to {approver.name}"
                )

            except Exception as e:
                _logger.error(f"Reminder failed for PR {pr.name}: {e}")


    def _notify_current_approver(self):
        self.ensure_one()

        if self.state != 'pending':
            return

        approver = self.current_approver_id
        # Check both the User email and the Partner email
        approver_email = approver.email or approver.partner_id.email

        if not approver or not approver.active:
            return

        if not approver_email:
            self.message_post(
                body=(
                    f"Approval reminder not sent. "
                    f"No email configured for approver {approver.name}."
                )
            )
            return

        template = self.env.ref(
            'material_purchase_requisition.mail_template_pr_approval_reminder',
            raise_if_not_found=False
        )

        if template:
            # Use email_layout_xmlid if you want the standard Odoo notification look
            # email_values helps force the recipient if the template's dynamic field fails
            email_values = {
                'email_to': approver_email,
                'reply_to': self.employee_id.user_id.email or self.company_id.email,
            }
            template.sudo().send_mail(self.id, force_send=True, email_values=email_values)

            self.last_reminder_sent_on = fields.Datetime.now()
        else:
            self.message_post(body="Approval reminder not sent. Mail template is missing.")

    def action_view_rfqs(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Related RFQs',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('pr_id', '=', self.id)],
            'context': {
                'default_pr_id': self.id,
            },
        }


     ### for mail sending to all followers if pr submitted
    # def _notify_followers_on_submit(self):
    #     template = self.env.ref(
    #         'material_purchase_requisition.mail_template_pr_submit',
    #         raise_if_not_found=False
    #     )
    #
    #     if not template:
    #         for rec in self:
    #             rec.message_post(body="⚠️ Template not found")
    #         return
    #
    #     for rec in self:
    #
    #         # -----------------------------
    #         # Ensure at least ONE follower
    #         # -----------------------------
    #         if rec.employee_id.user_id and rec.employee_id.user_id.partner_id:
    #             rec.message_subscribe(
    #                 partner_ids=[rec.employee_id.user_id.partner_id.id]
    #             )
    #
    #         # -----------------------------
    #         # Send to ALL followers
    #         # -----------------------------
    #         rec.message_post_with_source(
    #             template,
    #             subtype_xmlid="mail.mt_comment"  # 🔥 REQUIRED for email
    #         )

    def _notify_followers_on_submit(self):
        template = self.env.ref(
            'material_purchase_requisition.mail_template_pr_submit',
            raise_if_not_found=False
        )

        if not template:
            for rec in self:
                rec.message_post(body="⚠️ Template not found")
            return

        for rec in self:

            # ✅ Ensure employee is follower
            if rec.employee_id.user_id and rec.employee_id.user_id.partner_id:
                rec.message_subscribe(
                    partner_ids=[rec.employee_id.user_id.partner_id.id]
                )

            # ✅ Get followers with email
            partners = rec.message_partner_ids.filtered(lambda p: p.email)

            if not partners:
                rec.message_post(body="⚠️ No followers with email")
                continue

            # ✅ FORCE sending to followers
            rec.message_post_with_source(
                template,
                subtype_xmlid="mail.mt_comment",
                partner_ids=partners.ids  # 🔥 CRITICAL FIX
            )


class MaterialApprovalConfig(models.Model):
    _name = "material.approval.config"
    _description = "Material Approval Configuration"
    _order = "min_amount asc"

    min_amount = fields.Monetary(required=True,)
    max_amount = fields.Monetary(required=True,)
    approver_ids = fields.Many2many(
        "res.users",
        string="Additional Approvers",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        store=True,
    )


