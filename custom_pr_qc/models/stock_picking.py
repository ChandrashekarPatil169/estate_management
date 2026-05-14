from odoo import models,fields,api,_
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    qc_done_notified = fields.Boolean(default=False)


    def button_validate(self):
        # ⭐ ADMIN FULL BYPASS
        if self.env.user.has_group('base.group_system'):
            return super().button_validate()

        for rec in self:

            # -------------------------------------------------
            # Only for PR-based Purchase Orders
            # -------------------------------------------------
            if not (rec.purchase_id and rec.purchase_id.pr_id):
                continue

            # IMPORTANT → use sudo + no limit first
            qc = self.env['material.quality.check'].sudo().search([
                ('picking_id', '=', rec.id)
            ])

            # -------------------------------------------------
            # 1️⃣ CREATE QC ONLY IF NONE EXISTS
            # -------------------------------------------------
            if not qc:

                config = self.env['material.quality.config'].sudo().search([], limit=1)

                if not config:
                    raise UserError(_("QC Admins not configured"))

                qc = self.env['material.quality.check'].sudo().create({
                    'picking_id': rec.id,
                    'pr_id': rec.purchase_id.pr_id.id,
                    'requester_id': rec.purchase_id.pr_id.requisition_owner_id.id,
                    'admin_1_id': config.admin_checker_1.id,
                    'admin_2_id': config.admin_checker_2.id,
                })
                template = self.env.ref(
                    'custom_pr_qc.email_template_qc_notify',
                    raise_if_not_found=False
                )

                if not template:
                    rec.message_post(body="⚠️ QC Template not found")
                    return False

                users = [qc.requester_id, qc.admin_1_id, qc.admin_2_id]

                partner_ids = [
                    user.partner_id.id
                    for user in users
                    if user and user.partner_id
                ]

                if partner_ids:
                    rec.message_subscribe(partner_ids=partner_ids)

                partners = self.env['res.partner'].browse(partner_ids).filtered(lambda p: p.email)

                if not partners:
                    rec.message_post(body="⚠️ No QC users with email")
                    return False

                rec.message_post_with_source(
                    template,
                    subtype_xmlid="mail.mt_comment",
                    partner_ids=partners.ids
                )
                # Commit chatter log
                rec.message_post(
                    body=_("3-Way Quality Check created. Please complete QC before validating.")
                )

                return False  # stop validation cleanly

            # If multiple QC exists → use first one only
            qc = qc[0]

            # -------------------------------------------------
            # 2️⃣ CHECK QC RESULTS
            # -------------------------------------------------
            atleast_one_pass = False

            for move in rec.move_ids:

                qc_line = qc.line_ids.filtered(
                    lambda l: l.product_id.id == move.product_id.id
                )

                if not qc_line:
                    continue

                qc_line = qc_line[0]

                # ❌ REJECT
                if (
                        qc_line.req_result == 'reject'
                        or qc_line.inv_result == 'reject'
                        or qc_line.acc_result == 'reject'
                ):

                    for ml in move.move_line_ids:
                        ml.quantity = 0

                        # Identify who rejected
                    reject_user = ""
                    reject_role = ""

                    if qc_line.req_result == 'reject':
                        reject_user = qc.requester_id.name
                        reject_role = "Requester"

                    elif qc_line.inv_result == 'reject':
                        reject_user = qc.admin_1_id.name
                        reject_role = "Inventory"

                    elif qc_line.acc_result == 'reject':
                        reject_user = qc.admin_2_id.name
                        reject_role = "Accounts"

                    product_name = move.product_id.display_name

                    message = _(
                        "Product Rejected: %s "
                        "Rejected By: %s (%s)"
                    ) % (product_name, reject_user, reject_role)

                    rec.purchase_id.message_post(body=message)
                    rec.message_post(body=message)

                    continue

                # ✅ PASS
                if (
                        qc_line.req_result == 'pass'
                        and qc_line.inv_result == 'pass'
                        and qc_line.acc_result == 'pass'
                ):
                    atleast_one_pass = True

                # ⏳ PENDING
                else:
                    raise UserError(
                        _("QC approval still pending for product: %s") %
                        move.product_id.display_name
                    )

            # -------------------------------------------------
            # 3️⃣ BLOCK IF ALL REJECTED
            # -------------------------------------------------
            if not atleast_one_pass:
                raise UserError(_("No product passed QC."))

        return super().button_validate()

    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            if rec.state == 'done' and not rec.qc_done_notified:
                rec._notify_pr_followers_qc_done()

        return res

    def _notify_pr_followers_qc_done(self):
        self.ensure_one()

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("🔥 QC DONE METHOD CALLED for %s", self.name)

        # -----------------------------------------
        # Validate PR
        # -----------------------------------------
        if not (self.purchase_id and self.purchase_id.pr_id):
            return

        pr = self.purchase_id.pr_id

        # -----------------------------------------
        # Get QC
        # -----------------------------------------
        qc = self.env['material.quality.check'].search([
            ('picking_id', '=', self.id)
        ], limit=1)

        # Only notify if QC completed
        if qc and qc.state != 'done':
            _logger.info("❌ QC not done, skipping")
            return

        # -----------------------------------------
        # Prevent duplicate notification
        # -----------------------------------------
        if self.qc_done_notified:
            _logger.info("⚠ Already notified")
            return

        # -----------------------------------------
        # Get PR followers (NO FILTER)
        # -----------------------------------------
        partners = pr.message_partner_ids

        _logger.info("📢 Followers: %s", partners)

        if not partners:
            pr.message_post(body="⚠️ No followers to notify")
            return

        # -----------------------------------------
        # Prepare product list
        # -----------------------------------------
        product_lines = [
            f"{m.product_id.display_name} ({m.product_uom_qty})"
            for m in self.move_ids
        ]

        product_html = "<br/>".join(product_lines)

        # -----------------------------------------
        # Load template
        # -----------------------------------------
        template = self.env.ref(
            'custom_pr_qc.email_template_qc_done',
            raise_if_not_found=False
        )

        if not template:
            pr.message_post(body="⚠️ QC Done Template not found")
            return

        # -----------------------------------------
        # SEND MAIL + CHATTER
        # -----------------------------------------
        pr.with_context(
            po_name=self.purchase_id.name,
            picking_name=self.name,
            products=product_html
        ).message_post_with_source(
            template,
            subtype_xmlid="mail.mt_comment",
            partner_ids=partners.ids
        )

        # -----------------------------------------
        # Mark as notified
        # -----------------------------------------
        self.qc_done_notified = True

        _logger.info("✅ QC DONE MAIL SENT")

    # @api.model
    # def _cron_qc_reminder(self):
    #
    #     today = fields.Date.today()
    #
    #     qcs = self.search([
    #         ('state', '=', 'pending')
    #     ])
    #
    #     template = self.env.ref(
    #         'custom_pr_qc.email_template_qc_reminder',
    #         raise_if_not_found=False
    #     )
    #
    #     if not template:
    #         return
    #
    #     for qc in qcs:
    #
    #         # جلوگیری duplicate same-day spam
    #         if qc.last_reminder_date == today:
    #             continue
    #
    #         picking = qc.picking_id
    #         if not picking:
    #             continue
    #
    #         pending_users = []
    #
    #         for line in qc.line_ids:
    #
    #             if line.req_result == 'pending':
    #                 pending_users.append(qc.requester_id)
    #
    #             if line.inv_result == 'pending':
    #                 pending_users.append(qc.admin_1_id)
    #
    #             if line.acc_result == 'pending':
    #                 pending_users.append(qc.admin_2_id)
    #
    #         # remove duplicates
    #         pending_users = list(set(pending_users))
    #
    #         partner_ids = [
    #             u.partner_id.id
    #             for u in pending_users
    #             if u and u.partner_id and u.partner_id.email
    #         ]
    #
    #         # -----------------------------
    #         # HANDLE NO USERS CASE
    #         # -----------------------------
    #         if not partner_ids:
    #             picking.message_post(
    #                 body="⚠️ QC Reminder skipped: No users with valid email."
    #             )
    #             continue
    #
    #         partners = self.env['res.partner'].browse(partner_ids)
    #
    #         # -----------------------------
    #         # SEND MAIL + CHATTER TEMPLATE
    #         # -----------------------------
    #         picking.message_post_with_source(
    #             template,
    #             subtype_xmlid="mail.mt_comment",
    #             partner_ids=partners.ids
    #         )
    #
    #         # -----------------------------
    #         # EXPLICIT CHATTER LOG
    #         # -----------------------------
    #         picking.message_post(
    #             body=_("🔔 QC Reminder sent to: %s") % ", ".join(partners.mapped('name'))
    #         )
    #
    #         # -----------------------------
    #         # UPDATE DATE
    #         # -----------------------------
    #         qc.last_reminder_date = today
# def button_validate(self):
#
#     for rec in self:
#
#         if not (rec.purchase_id and rec.purchase_id.pr_id):
#             continue
#
#         qc = self.env['material.quality.check'].search(
#             [('picking_id', '=', rec.id)], limit=1
#         )
#
#         # ------------------------------
#         # CREATE QC IF NOT EXISTS
#         # ------------------------------
#         if not qc:
#
#             config = self.env['material.quality.config'].sudo().search([], limit=1)
#
#             if not config:
#                 raise UserError("QC Admins not configured")
#
#             qc = self.env['material.quality.check'].sudo().create({
#                 'picking_id': rec.id,
#                 'pr_id': rec.purchase_id.pr_id.id,
#                 'requester_id': rec.purchase_id.pr_id.requisition_owner_id.id,
#                 'admin_1_id': config.admin_checker_1.id,
#                 'admin_2_id': config.admin_checker_2.id,
#             })
#
#             # SEND EMAIL
#             template = self.env.ref('custom_pr_qc.email_template_qc_notify')
#             for user in [qc.requester_id, qc.admin_1_id, qc.admin_2_id]:
#                 if user.email:
#                     template.sudo().send_mail(
#                         qc.id,
#                         force_send=True,
#                         email_values={'email_to': user.email}
#                     )
#
#             return {
#                 'name': 'Quality Check Required',
#                 'type': 'ir.actions.act_window',
#                 'res_model': 'qc.status.wizard',
#                 'view_mode': 'form',
#                 'target': 'new',
#                 'context': {'default_qc_id': qc.id}
#             }
#
#         # ------------------------------
#         # PRODUCT-WISE VALIDATION
#         # ------------------------------
#         pending_found = False
#         atleast_one_pass = False
#
#         for move in rec.move_ids:
#
#             qc_line = qc.line_ids.filtered(
#                 lambda l: l.product_id.id == move.product_id.id
#             )
#
#             if not qc_line:
#                 continue
#
#             qc_line = qc_line[0]
#
#             # ---------- ANY REJECT ----------
#             if (
#                     qc_line.req_result == 'reject'
#                     or qc_line.inv_result == 'reject'
#                     or qc_line.acc_result == 'reject'
#             ):
#                 for ml in move.move_line_ids:
#                     ml.quantity = 0
#                 continue
#
#             # ---------- ALL PASS ----------
#             if (
#                     qc_line.req_result == 'pass'
#                     and qc_line.inv_result == 'pass'
#                     and qc_line.acc_result == 'pass'
#             ):
#                 atleast_one_pass = True
#                 continue
#
#             # ---------- STILL PENDING ----------
#             pending_found = True
#
#         # ------------------------------
#         # BLOCK IF ANY PENDING EXISTS
#         # ------------------------------
#         if pending_found:
#             return {
#                 'name': 'Quality Check Required',
#                 'type': 'ir.actions.act_window',
#                 'res_model': 'qc.status.wizard',
#                 'view_mode': 'form',
#                 'target': 'new',
#                 'context': {'default_qc_id': qc.id}
#             }
#
#         # ------------------------------
#         # BLOCK IF NOTHING PASSED
#         # ------------------------------
#         if not atleast_one_pass:
#             raise UserError("No product passed QC.")
#
#     return super().button_validate()
