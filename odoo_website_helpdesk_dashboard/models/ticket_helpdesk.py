# -*- coding: utf-8 -*-

import calendar
from odoo import api, models


class TicketHelpdesk(models.Model):
    _inherit = 'helpdesk.ticket'

    # -------------------------------------------------
    # Helper function for ticket domain
    # -------------------------------------------------
    def _get_ticket_domain(self):
        user = self.env.user
        is_privileged = (
                user.has_group('base.group_system') or
                user.has_group('department_helpdesk.group_helpdesk_department_manager')
        )

        return [] if is_privileged else [('assign_to', '=', user.id)]

    # -------------------------------------------------
    # Dashboard Counts
    # -------------------------------------------------
    @api.model
    def get_tickets_count(self):

        domain = self._get_ticket_domain()
        print('0000000000000', domain)

        ticket_details = self.search(domain)

        ticket_data = [
            {
                'ticket_name': ticket.name,
                'customer_name': ticket.requested_person_id.name,
                'request_title': ticket.request_title,
                'priority': ticket.priority,
                'assigned_to': ticket.assign_to.name,
                'assigned_image': ticket.assign_to.image_1920,
            }
            for ticket in ticket_details
        ]

        tickets_new_count = self.search_count(domain + [('stage_id.name', '=', 'New')])
        tickets_in_progress_count = self.search_count(domain + [('stage_id.name', '=', 'In Progress')])
        tickets_closed_count = self.search_count(domain + [('stage_id.name', '=', 'Done')])

        very_low = self.search_count(domain + [('priority', '=', '0')]) * 10
        low = self.search_count(domain + [('priority', '=', '1')]) * 10
        normal = self.search_count(domain + [('priority', '=', '2')]) * 10
        high = self.search_count(domain + [('priority', '=', '3')]) * 10
        very_high = self.search_count(domain + [('priority', '=', '4')]) * 10

        teams_count = self.env['helpdesk.ticket.team'].search_count([])

        tickets = self.search(domain + [('stage_id.name', '=', 'New')])
        p_tickets = [ticket.name for ticket in tickets]

        values = {
            'inbox_count': tickets_new_count,
            'progress_count': tickets_in_progress_count,
            'done_count': tickets_closed_count,
            'team_count': teams_count,
            'p_tickets': p_tickets,
            'very_low_count1': very_low,
            'low_count1': low,
            'normal_count1': normal,
            'high_count1': high,
            'very_high_count1': very_high,
            'ticket_details': ticket_data,
        }

        return values

    # -------------------------------------------------
    # Ticket View
    # -------------------------------------------------
    @api.model
    def get_tickets_view(self):

        domain = self._get_ticket_domain()

        tickets_new = self.search(domain + [('stage_id.name', '=', 'New')])
        tickets_progress = self.search(domain + [('stage_id.name', '=', 'In Progress')])
        tickets_done = self.search(domain + [('stage_id.name', '=', 'Done')])

        teams = self.env['helpdesk.ticket.team'].search([])

        new_list = [f"{t.name} : {t.request_title}" for t in tickets_new]
        progress_list = [f"{t.name} : {t.request_title}" for t in tickets_progress]
        done_list = [f"{t.name} : {t.request_title}" for t in tickets_done]
        teams_list = [team.name for team in teams]

        values = {
            'inbox_count': len(tickets_new),
            'progress_count': len(tickets_progress),
            'done_count': len(tickets_done),
            'team_count': len(teams),
            'new_tkts': new_list,
            'progress': progress_list,
            'done': done_list,
            'teams': teams_list,
        }

        return values

    # -------------------------------------------------
    # Monthly Chart
    # -------------------------------------------------
    @api.model
    def get_ticket_month_pie(self):

        domain = self._get_ticket_domain()

        tickets = self.search(domain)

        month_count = []
        month_value = []

        for rec in tickets:
            month = rec.create_date.month

            if month not in month_value:
                month_value.append(month)

            month_count.append(month)

        month_val = []

        for m in month_value:
            value = month_count.count(m)
            month_name = calendar.month_name[m]

            month_val.append({
                'label': month_name,
                'value': value
            })

        name = [record['label'] for record in month_val]
        count = [record['value'] for record in month_val]

        return [count, name]

    # -------------------------------------------------
    # Team Chart
    # -------------------------------------------------
    @api.model
    def get_team_ticket_count_pie(self):

        domain = self._get_ticket_domain()

        tickets = self.search(domain)

        team_list = []
        ticket_count = []

        for rec in tickets:
            if rec.team_id:
                team = rec.team_id.name

                if team not in team_list:
                    team_list.append(team)

                ticket_count.append(team)

        team_val = []

        for team in team_list:
            value = ticket_count.count(team)

            team_val.append({
                'label': team,
                'value': value
            })

        name = [record['label'] for record in team_val]
        count = [record['value'] for record in team_val]

        return [count, name]