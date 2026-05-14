# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.purchase.controllers.portal import CustomerPortal


class VendorPurchasePortal(CustomerPortal):

    @http.route(
        ['/my/purchase/<int:order_id>/acknowledge'],
        type='http',
        auth="user",
        methods=['POST'],
        website=True,
        csrf=True
    )
    def portal_rfq_acknowledge(self, order_id, decision=None, **post):
        """ Handles the vendor's acceptance or rejection of an RFQ from the portal. """

        # 1. Secure Access Check (Standard Odoo Portal Security)
        try:
            # This method verifies if the logged-in portal user has rights to this specific PO
            order_sudo = self._document_check_access('purchase.order', order_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # 2. Logic Check: Only allow if in the correct state
        # Ensure these fields and states exist in your purchase.order model
        if order_sudo.state not in ['sent', 'vendor_pending']:
            return request.redirect(order_sudo.get_portal_url())

        # 3. Handle Decision
        if decision == 'accept':
            order_sudo.write({
                'vendor_decision': 'yes',
                'vendor_decision_date': fields.Date.today(),
            })
            order_sudo.message_post(body=_("Vendor accepted this RFQ via the portal."))

        elif decision == 'reject':
            reason = post.get('reject_reason')
            order_sudo.write({
                'vendor_decision': 'no',
                'vendor_decision_date': fields.Date.today(),
                'vendor_reject_reason': reason,
            })
            order_sudo.message_post(
                body=_("Vendor rejected this RFQ. Reason: %s") % reason
            )

        # 4. Redirect back to the Purchase Order portal page
        return request.redirect(order_sudo.get_portal_url())


