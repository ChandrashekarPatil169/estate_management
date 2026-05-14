# -*- coding: utf-8 -*-

import calendar
from odoo import api, models


class ExternalTicketDashboard(models.Model):
    """
    Extends helpdesk.ticket to provide dashboard data for External Ticketing.

    NOTE: 'is_external_ticket' is purely a UI context flag — NOT a stored
    field on helpdesk.ticket. External tickets are identified by having
    hup_project_id set (Many2one to project.project.custom).
    """
    _inherit = 'helpdesk.ticket'

    # ------------------------------------------------------------------
    # Access helper
    # ------------------------------------------------------------------
    def _get_ext_ticket_domain(self):
        """
        Base domain: tickets that have an external project linked.
        Admins / managers see all; others only see their own.
        """
        user = self.env.user
        is_privileged = (
            user.has_group('base.group_system') or
            user.has_group('department_helpdesk.group_helpdesk_department_manager')
        )
        # External tickets = those with an external project assigned
        base = [('hup_project_id', '!=', False)]
        if not is_privileged:
            base.append(('assign_to', '=', user.id))
        return base

    # ------------------------------------------------------------------
    # KPI counts (stat cards)
    # ------------------------------------------------------------------
    @api.model
    def get_ext_tickets_count(self):
        """Return all KPI counts for the External Ticketing dashboard."""
        domain = self._get_ext_ticket_domain()

        # Stage counts
        new_count = self.search_count(domain + [('stage_id.name', '=', 'New')])
        progress_count = self.search_count(domain + [('stage_id.name', '=', 'In Progress')])
        resolved_count = self.search_count(domain + [('stage_id.name', '=', 'Resolved')])
        done_count = self.search_count(domain + [('stage_id.name', '=', 'Done')])

        # Priority counts as percentage of total
        total = self.search_count(domain) or 1
        priority_levels = [
            ('0', 'very_low'),
            ('1', 'low'),
            ('2', 'normal'),
            ('3', 'high'),
            ('4', 'very_high'),
        ]
        priority_counts = {}
        for level, label in priority_levels:
            cnt = self.search_count(domain + [('priority', '=', level)])
            priority_counts[label] = round((cnt / total) * 100)

        # Global project / subproject counts
        project_count = self.env['project.project.custom'].search_count([])
        subproject_count = self.env['project.subproject'].search_count([])

        # Ticket detail rows for the table (latest 50)
        tickets = self.search(domain, limit=50, order='create_date desc')
        ticket_data = []
        for ticket in tickets:
            ticket_data.append({
                'id': ticket.id,
                'ticket_name': ticket.name or '',
                'request_title': ticket.request_title or '',
                'customer_name': ticket.requested_person_id.name if ticket.requested_person_id else '',
                'project': ticket.hup_project_id.name if ticket.hup_project_id else '',
                'subproject': ticket.hup_subproject_id.name if ticket.hup_subproject_id else '',
                'priority': ticket.priority or '0',
                'stage': ticket.stage_id.name or '',
                'assigned_to': ticket.assign_to.name if ticket.assign_to else '',
                'assigned_image': ticket.assign_to.image_128 if ticket.assign_to else False,
            })

        return {
            'new_count': new_count,
            'progress_count': progress_count,
            'resolved_count': resolved_count,
            'done_count': done_count,
            'project_count': project_count,
            'subproject_count': subproject_count,
            'priority_counts': priority_counts,
            'ticket_data': ticket_data,
            'total_count': self.search_count(domain),
        }

    # ------------------------------------------------------------------
    # Monthly trend chart
    # ------------------------------------------------------------------
    @api.model
    def get_ext_ticket_monthly(self):
        """Return [counts_list, month_labels] for the monthly line chart."""
        domain = self._get_ext_ticket_domain()
        tickets = self.search(domain)

        month_map = {}
        for ticket in tickets:
            m = ticket.create_date.month
            month_map[m] = month_map.get(m, 0) + 1

        sorted_months = sorted(month_map.keys())
        labels = [calendar.month_abbr[m] for m in sorted_months]
        counts = [month_map[m] for m in sorted_months]
        return [counts, labels]

    # ------------------------------------------------------------------
    # Project-wise ticket count chart
    # ------------------------------------------------------------------
    @api.model
    def get_ext_project_ticket_count(self):
        """Return [counts_list, project_name_list] for the project bar chart."""
        domain = self._get_ext_ticket_domain()
        tickets = self.search(domain)

        project_map = {}
        for ticket in tickets:
            if ticket.hup_project_id:
                name = ticket.hup_project_id.name
                project_map[name] = project_map.get(name, 0) + 1

        labels = list(project_map.keys())
        counts = list(project_map.values())
        return [counts, labels]

    # ------------------------------------------------------------------
    # Stage distribution doughnut chart
    # ------------------------------------------------------------------
    @api.model
    def get_ext_stage_distribution(self):
        """Return stage breakdown for the doughnut chart."""
        domain = self._get_ext_ticket_domain()
        stages = ['New', 'In Progress', 'Resolved', 'Done']
        counts = [
            self.search_count(domain + [('stage_id.name', '=', s)])
            for s in stages
        ]
        return [counts, stages]
