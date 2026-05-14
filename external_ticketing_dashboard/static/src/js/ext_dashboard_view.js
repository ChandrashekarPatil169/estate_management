/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

/**
 * External Ticketing Dashboard OWL Component
 *
 * Mirrors the existing HelpDeskDashBoard component from odoo_website_helpdesk_dashboard
 * but is scoped entirely to external tickets (is_external_ticket = True).
 */
class ExtTicketingDashboard extends Component {
    setup() {
        super.setup();

        this.ref = useRef("extTicketDashboard");
        this.actionService = useService("action");
        this.orm = useService("orm");

        onWillStart(async () => {
            const [isSystem, isManager] = await Promise.all([
                user.hasGroup("base.group_system"),
                user.hasGroup("department_helpdesk.group_helpdesk_department_manager"),
            ]);
            this.isPrivilegedUser = isSystem || isManager;
        });

        onMounted(() => {
            this._renderDashboard();
            this._renderGraphs();
        });
    }

    // ----------------------------------------------------------------
    // RPC helper — calls a method on helpdesk.ticket
    // ----------------------------------------------------------------
    _callTicket(method) {
        return rpc("/web/dataset/call_kw/helpdesk.ticket/" + method, {
            model: "helpdesk.ticket",
            method: method,
            args: [],
            kwargs: {},
        });
    }

    // ----------------------------------------------------------------
    // Render stat cards + priority bars + ticket table
    // ----------------------------------------------------------------
    async _renderDashboard() {
        const el = this.ref.el;
        const data = await this._callTicket("get_ext_tickets_count");

        // KPI Cards
        this._setText(el, "#ext_new_count", data.new_count);
        this._setText(el, "#ext_progress_count", data.progress_count);
        this._setText(el, "#ext_resolved_count", data.resolved_count);
        this._setText(el, "#ext_done_count", data.done_count);
        this._setText(el, "#ext_project_count", data.project_count);
        this._setText(el, "#ext_subproject_count", data.subproject_count);

        // Priority bars
        const priorities = ["very_low", "low", "normal", "high", "very_high"];
        priorities.forEach((p) => {
            const pct = (data.priority_counts && data.priority_counts[p]) || 0;
            const bar = el.querySelector("." + p + "_count");
            const label = el.querySelector("." + p + "_pct");
            if (bar) bar.style.width = pct + "%";
            if (label) label.textContent = pct + "%";
        });

        // Ticket table
        const tbody = el.querySelector("#ext_ticket_tbody");
        if (tbody) {
            tbody.innerHTML = "";
            if (!data.ticket_data || data.ticket_data.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-3">No external tickets found.</td></tr>`;
            } else {
                data.ticket_data.forEach((ticket) => {
                    const priorityMap = {
                        "0": "Very Low", "1": "Low", "2": "Normal",
                        "3": "High", "4": "Very High",
                    };
                    const avatarHtml = ticket.assigned_image
                        ? `<img src="data:image/png;base64,${ticket.assigned_image}"
                               class="ext-user-avatar" alt=""/>`
                        : `<span class="ext-user-avatar ext-no-avatar"><i class="fa fa-user"/></span>`;

                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><a href="#" class="ext-ticket-link" data-id="${ticket.id}">${ticket.ticket_name || ''}</a></td>
                        <td>${ticket.request_title || ''}</td>
                        <td>${ticket.customer_name || ''}</td>
                        <td>${ticket.project || '<span class="text-muted">—</span>'}</td>
                        <td>${ticket.subproject || '<span class="text-muted">—</span>'}</td>
                        <td><span class="ext-priority-badge ext-p-${ticket.priority}">${priorityMap[ticket.priority] || ticket.priority}</span></td>
                        <td><span class="ext-stage-badge">${ticket.stage || ''}</span></td>
                        <td class="ext-assigned-cell">${avatarHtml} ${ticket.assigned_to || ''}</td>
                    `;
                    // Click on ticket name → open form
                    tr.querySelector(".ext-ticket-link").addEventListener("click", (e) => {
                        e.preventDefault();
                        this.actionService.doAction({
                            type: "ir.actions.act_window",
                            res_model: "helpdesk.ticket",
                            res_id: ticket.id,
                            views: [[false, "form"]],
                            target: "current",
                            context: { is_external_ticket: true },
                        });
                    });
                    tbody.appendChild(tr);
                });
            }
        }
    }

    // ----------------------------------------------------------------
    // Render all three charts
    // ----------------------------------------------------------------
    _renderGraphs() {
        this._renderStageChart();
        this._renderProjectChart();
        this._renderMonthlyChart();
    }

    // Doughnut — Stage distribution
    async _renderStageChart() {
        const el = this.ref.el;
        const ctx = el.querySelector("#ext_stage_chart");
        if (!ctx) return;

        const [counts, labels] = await this._callTicket("get_ext_stage_distribution");

        new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: counts,
                    backgroundColor: ["#706F8E", "#f6a623", "#5b9bd5", "#2ecc71"],
                    borderColor: ["#555", "#c47d00", "#3a7ab5", "#27ae60"],
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                legend: {
                    display: true,
                    position: "right",
                    labels: { fontColor: "#333", fontSize: 12 },
                },
                scales: {
                    yAxes: [{
                        gridLines: { display: false },
                        ticks: { display: false },
                    }],
                },
            },
        });
    }

    // Bar — Tickets by project
    async _renderProjectChart() {
        const el = this.ref.el;
        const ctx = el.querySelector("#ext_project_chart");
        if (!ctx) return;

        const [counts, labels] = await this._callTicket("get_ext_project_ticket_count");
        const colors = [
            "rgba(102,113,154,0.7)", "rgba(246,166,35,0.7)", "rgba(91,155,213,0.7)",
            "rgba(46,204,113,0.7)", "rgba(231,76,60,0.7)", "rgba(155,89,182,0.7)",
        ];

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels.length ? labels : ["No Data"],
                datasets: [{
                    label: "Tickets",
                    data: counts.length ? counts : [0],
                    backgroundColor: colors.slice(0, labels.length || 1),
                    borderColor: colors.slice(0, labels.length || 1).map(c => c.replace("0.7", "1")),
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                legend: { display: false },
                scales: {
                    yAxes: [{
                        ticks: { beginAtZero: true, stepSize: 1 },
                    }],
                },
            },
        });
    }

    // Line — Monthly trend
    async _renderMonthlyChart() {
        const el = this.ref.el;
        const ctx = el.querySelector("#ext_monthly_chart");
        if (!ctx) return;

        const [counts, labels] = await this._callTicket("get_ext_ticket_monthly");

        new Chart(ctx, {
            type: "line",
            data: {
                labels: labels.length ? labels : ["No Data"],
                datasets: [{
                    label: "External Tickets Created",
                    data: counts.length ? counts : [0],
                    backgroundColor: "rgba(74, 92, 154, 0.15)",
                    borderColor: "#4a5c9a",
                    borderWidth: 2,
                    pointBackgroundColor: "#4a5c9a",
                    fill: true,
                    tension: 0.4,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                legend: {
                    display: true,
                    position: "top",
                    labels: { fontColor: "#333", fontSize: 12 },
                },
                scales: {
                    yAxes: [{
                        ticks: { beginAtZero: true, stepSize: 1 },
                    }],
                },
            },
        });
    }

    // ----------------------------------------------------------------
    // Utility
    // ----------------------------------------------------------------
    _setText(root, selector, value) {
        const el = root.querySelector(selector);
        if (el) el.textContent = value !== undefined ? value : "—";
    }

    // ----------------------------------------------------------------
    // Navigation actions
    // ----------------------------------------------------------------
    _openExternalTickets(stageName, title) {
        const userId = user.userId;
        let domain = [["hup_project_id", "!=", false]];
        if (stageName) {
            domain.push(["stage_id.name", "=", stageName]);
        }
        if (!this.isPrivilegedUser) {
            domain.push(["assign_to", "=", userId]);
        }
        this.actionService.doAction({
            name: _t(title),
            type: "ir.actions.act_window",
            res_model: "helpdesk.ticket",
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: { is_external_ticket: true },
            target: "current",
        });
    }

    openNewTickets(ev) {
        ev.preventDefault();
        this._openExternalTickets("New", "New External Tickets");
    }

    openProgressTickets(ev) {
        ev.preventDefault();
        this._openExternalTickets("In Progress", "External Tickets In Progress");
    }

    openResolvedTickets(ev) {
        ev.preventDefault();
        this._openExternalTickets("Resolved", "Resolved External Tickets");
    }

    openDoneTickets(ev) {
        ev.preventDefault();
        this._openExternalTickets("Done", "Done External Tickets");
    }

    openProjects(ev) {
        ev.preventDefault();
        this.actionService.doAction({
            name: _t("External Projects"),
            type: "ir.actions.act_window",
            res_model: "project.project.custom",
            view_mode: "list,kanban,form",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            target: "current",
        });
    }

    openSubprojects(ev) {
        ev.preventDefault();
        this.actionService.doAction({
            name: _t("External Subprojects"),
            type: "ir.actions.act_window",
            res_model: "project.subproject",
            view_mode: "list,kanban,form",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            target: "current",
        });
    }
}

ExtTicketingDashboard.template = "DashBoardExtTicketing";
registry.category("actions").add("ext_ticketing_dashboard", ExtTicketingDashboard);
