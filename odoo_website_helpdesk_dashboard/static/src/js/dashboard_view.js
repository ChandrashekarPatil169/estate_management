/** @odoo-module **/
import { registry } from "@web/core/registry";
import { rpc } from '@web/core/network/rpc';
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart } from "@odoo/owl";
import { onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
/** Initializes the HelpDeskDashBoard component**/
class HelpDeskDashBoard extends Component{
    /**Set up function**/
    setup() {
        super.setup();

        this.ref = useRef("helpDeskDashboard");
        this.actionService = useService("action");
        this.orm = useService("orm");

        onWillStart(async () => {
            const [isSystemUser, isManagerUser] = await Promise.all([
                user.hasGroup("base.group_system"),
                user.hasGroup("department_helpdesk.group_helpdesk_department_manager")
            ]);

            this.isPrivilegedUser = isSystemUser || isManagerUser;

            console.log("Admin:", isSystemUser);
            console.log("Manager:", isManagerUser);
            console.log("Privileged:", this.isPrivilegedUser);
        });

        onMounted(() => {
            this.render_dashboards();
            this.render_graphs();
        });
    }
    /**To render the charts**/
    render_graphs() {
        var self = this;
        self.render_tickets_month_graph();
        self.render_team_ticket_count_graph();
    }
    /**Doughnut chart: TICKET STATUS**/
    render_tickets_month_graph() {
        var self = this;
        var ctx = this.ref.el.querySelector('#ticket_month')
        rpc('/web/dataset/call_kw/helpdesk.ticket/get_tickets_count', {
            model: "helpdesk.ticket",
            method: "get_tickets_view",
             args: [],
            kwargs: {},
        }).then(function (values) {
            var data = {
                labels: ['New', 'In Progress', 'Done'],
                datasets: [{
                    data: [values.inbox_count, values.progress_count, values.done_count],
                    backgroundColor: [
                        "#665191",
                        "#ff7c43",
                        "#ffa600"
                    ],
                    borderColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a"
                    ],
                    borderWidth: 1
                }]
            };
            /** Options **/
            var options = {
                responsive: true,
                title: false,
                legend: {
                    display: true,
                    position: "right",
                    labels: {
                        fontColor: "#333",
                        fontSize: 16
                    }
                },
                scales: {
                    yAxes: [{
                        gridLines: {
                            color: "rgba(0, 0, 0, 0)",
                            display: false,
                        },
                        ticks: {
                            min: 0,
                            display: false,
                        }
                    }]
                }
            };
            /** Create Chart class object **/
            var chart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: options
            });
        });
    }
    /** Bar chart: Team - Tickets Count Ratio **/
    render_team_ticket_count_graph() {
        var self = this
        var ctx = this.ref.el.querySelector('.team_ticket_count');
        rpc('/web/dataset/call_kw/helpdesk.ticket/get_tickets_count', {
            model: "helpdesk.ticket",
            method: "get_team_ticket_count_pie",
             args: [],
            kwargs: {},
        }).then(function (arrays) {
            var data = {
                labels: arrays[1],
                datasets: [{
                    label: "",
                    data: arrays[0],
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(255, 159, 64, 0.2)',
                        'rgba(255, 205, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                       'rgba(153, 102, 255, 0.2)',
                        'rgba(201, 203, 207, 0.2)'
                    ],
                    borderColor: ['rgb(255, 99, 132)',
                        'rgb(255, 159, 64)',
                        'rgb(255, 205, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(54, 162, 235)',
                        'rgb(153, 102, 255)',
                        'rgb(201, 203, 207)'
                    ],
                    borderWidth: 1
                },]
            };
            /** Options **/
            var options = {
                responsive: true,
                title: false,
                maintainAspectRatio: true,
                legend: {
                    display: false
                },
                scales: {
                    yAxes: [{
                        display: true,
                        ticks: {
                            beginAtZero: true,
                            steps: 10,
                            stepValue: 5,
                            // max: 100
                        }
                    }]
                }
            };
            /** Create Chart class object **/
            var chart = new Chart(ctx, {
                type: "bar",
                data: data,
                options: options
            });
        });
    }
    /** List view of tickets in dashboard **/
    render_dashboards() {
        var self = this;
        rpc('/web/dataset/call_kw/helpdesk.ticket/get_tickets_count', {
            model: 'helpdesk.ticket',
            method: 'get_tickets_count',
            args: [],
            kwargs: {},
        }).then(function(result) {
            var inbox_count_span = document.createElement("span");
            inbox_count_span.textContent = result.inbox_count
            self.ref.el.querySelector('#inbox_count').appendChild(inbox_count_span);
            var progress_count_span = document.createElement("span");
            progress_count_span.textContent = result.progress_count
            self.ref.el.querySelector('#inprogress_count').appendChild(progress_count_span);
            var done_count_span = document.createElement("span");
            done_count_span.textContent = result.done_count
            self.ref.el.querySelector('#done_count').appendChild(done_count_span);
            // var team_count_span = document.createElement("span");
            // team_count_span.textContent = result.team_count
            // self.ref.el.querySelector('#team_count').appendChild(team_count_span);
            var priorityCounts = {
                very_low: result.very_low_count1,
                low: result.low_count1,
                normal: result.normal_count1,
                high: result.high_count1,
                very_high : result.very_high_count1
            };
            /**Loop through the priorities and create progress bars**/
            for (var priority in priorityCounts) {
                var progressBarWidth = priorityCounts[priority] + "%";
                var progressBar = $("<div class='progress-bar'></div>").css("width", progressBarWidth);
                var progressBarContainer = $("<div class='progress'></div>").append(progressBar);
                var progressValue = $("<div class='progress-value'></div>").text(priorityCounts[priority] + "%");
                // Append the progress bar container to elements with class corresponding to the priority
                $("." + priority + "_count").append(progressBarContainer);
                $("." + priority + "_count .progress-value").append(progressValue);
            }
            var tbody = $(".ticket-details");
            var ticket_details = result.ticket_details;
            for (var i = 0; i < ticket_details.length; i++) {
                 /** Get the current ticket object **/
                var ticket = ticket_details[i];
                var row = $("<tr></tr>");
                /** Assuming you have the Base64-encoded image data in a
                variable called ticket.assigned_image **/
                var base64Image = ticket.assigned_image;
                var assignedUserCell = $("<td class='td'></td>");
                var imgElement = $("<img>");
                /** Set the image source **/
                imgElement.attr("src", "data:image/png;base64," + base64Image);
                /** Set an alt attribute for accessibility **/
                imgElement.attr("alt", "User Image");
                /** Add the 'oe-avatar' class to the <img> element **/
                imgElement.addClass("user-image");

                /** Append the img element to the assignedUserCell **/
                assignedUserCell.append(imgElement);
                /** Append the assignedUserCell to the row **/
                row.append(assignedUserCell);
                row.append("<td class='td'>" + ticket.customer_name + "</td>");
                row.append("<td class='td'>" + ticket.ticket_name + "</td>");
                row.append(assignedUserCell);
                row.append("<td>" + ticket.assigned_to + "</td>");
                row.append("<td>" + ticket.subject + "</td>");
                row.append("<td>" + ticket.priority + "</td>");
                tbody.append(row);
            }
            $(".response").append(result.response);
            rpc('/help/tickets', {}).then((values) => {
                $('.pending_tickets').append(values);
            });
        });
    }
    openTickets(stageName, title) {
        const userId = user.userId;

        let domain = [['stage_id.name', '=', stageName]];

        if (!this.isPrivilegedUser) {
            domain.push(['assign_to', '=', userId]);
        }

        this.actionService.doAction({
            name: _t(title),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current'
        });
    }
    /** To show new tickets **/
    tickets_inbox(ev) {
        ev.preventDefault();
        this.openTickets('New', 'Inbox');
    }
    /** To show in progress tickets **/
    tickets_inprogress(ev) {
        ev.preventDefault();
        this.openTickets('In Progress', 'In Progress');
    }
    /** To show done tickets **/
    tickets_done(ev) {
        ev.preventDefault();
        this.openTickets('Done', 'Done');
    }
    /** To show the helpdesk teams**/
     helpdesk_teams(ev) {
         var self = this;
         ev.stopPropagation();
         ev.preventDefault();
         self.actionService.doAction({
             name: _t("Teams"),
             type: 'ir.actions.act_window',
             res_model: 'helpdesk.ticket.team',
             view_mode: 'list,form',
             views: [[false, 'list'], [false, 'form']],
             target: 'current'
         });
     }
}
HelpDeskDashBoard.template = 'DashBoardHelpDesk'
registry.category("actions").add("helpdesk_dashboard", HelpDeskDashBoard)
