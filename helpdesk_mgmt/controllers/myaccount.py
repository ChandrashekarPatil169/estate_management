# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from collections import OrderedDict
from operator import itemgetter

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.tools import groupby as groupbyelem
from odoo.fields import Domain
# ✅ correct for Odoo 19

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class CustomerPortalHelpdesk(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "ticket_count" in counters:
            helpdesk_model = request.env["helpdesk.ticket"]
            ticket_count = (
                helpdesk_model.search_count([])
                if helpdesk_model.has_access("read")
                else 0
            )
            values["ticket_count"] = ticket_count
        return values

    @http.route(
        ["/my/tickets", "/my/tickets/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_tickets(
            self,
            page=1,
            date_begin=None,
            date_end=None,
            sortby=None,
            filterby=None,
            search=None,
            search_in=None,
            groupby=None,
            **kw,
    ):
        HelpdeskTicket = request.env["helpdesk.ticket"]

        if not HelpdeskTicket.has_access("read"):
            return request.redirect("/my")

        values = self._prepare_portal_layout_values()

        searchbar_sortings = dict(
            sorted(
                self._ticket_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )

        searchbar_filters = {
            "all": {"label": request.env._("All"), "domain": []},
        }

        for stage in request.env["helpdesk.ticket.stage"].search([]):
            searchbar_filters[str(stage.id)] = {
                "label": stage.name,
                "domain": [("stage_id", "=", stage.id)],
            }

        if not sortby:
            sortby = "date"

        if not filterby:
            filterby = "all"

        domain = searchbar_filters.get(filterby)["domain"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        if search:
            domain += self._ticket_get_search_domain(search_in or "all", search)

        # ✅ FIXED: use expression.AND instead of AND
        domain = Domain.AND([
            domain,
            request.env["ir.rule"]._compute_domain(HelpdeskTicket._name, "read"),
        ])

        ticket_count = HelpdeskTicket.search_count(domain)

        pager = portal_pager(
            url="/my/tickets",
            total=ticket_count,
            page=page,
            step=self._items_per_page,
        )

        tickets = HelpdeskTicket.search(
            domain,
            order="create_date desc",
            limit=self._items_per_page,
            offset=pager["offset"],
        )

        values.update({
            "tickets": tickets,
            "pager": pager,
            "page_name": "ticket",
        })

        return request.render("helpdesk_mgmt.portal_my_tickets", values)

    def _ticket_get_searchbar_sortings(self):
        return {
            "date": {
                "label": request.env._("Newest"),
                "order": "create_date desc",
                "sequence": 1,
            },
            "name": {
                "label": request.env._("Title"),
                "order": "name",
                "sequence": 2,
            },
        }

    def _ticket_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("number", "all"):
            search_domain.append([("number", "ilike", search)])
        if search_in in ("name", "all"):
            search_domain.append([("name", "ilike", search)])

        # ✅ FIXED: use expression.OR instead of OR
        return Domain.OR(search_domain)

