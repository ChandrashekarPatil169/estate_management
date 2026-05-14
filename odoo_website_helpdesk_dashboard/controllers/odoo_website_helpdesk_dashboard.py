from odoo import http
from odoo.http import request


class HelpDeskTickets(http.Controller):

    @http.route(['/help/tickets'], type="jsonrpc", auth="user")
    def elearning_snippet(self):

        # Check dashboard access
        if not request.env.user.has_group(
            'department_helpdesk.group_helpdesk_dashboard_access'
        ):
            return {'error': 'Access Denied'}

        tickets = []

        help_tickets = request.env['helpdesk.ticket'].sudo().search([
            ('stage_id.name', '=', 'Inbox')
        ])

        for i in help_tickets:
            tickets.append({
                'name': i.name,
                'subject': i.subject,
                'id': i.id
            })

        values = {
            'h_tickets': tickets
        }

        response = http.Response(
            template='odoo_website_helpdesk_dashboard.dashboard_tickets',
            qcontext=values
        )

        return response.render()