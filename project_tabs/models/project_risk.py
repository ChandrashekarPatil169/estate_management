# models/project_risk.py

from odoo import models, fields, api

class ProjectRisk(models.Model):
    _name = 'project.risk'
    _description = 'Project Risk'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'risk_title'

    # Link to project
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=True,
        ondelete='cascade'
    )

    # Risk Identification
    risk_title = fields.Char(string="Risk Title", required=True, tracking=True)
    risk_description = fields.Text(string="Risk Description")

    risk_category = fields.Selection([
        ('technical', 'Technical'),
        ('business', 'Business'),
        ('schedule', 'Schedule'),
        ('resource', 'Resource'),
        ('dependency', 'Dependency'),
        ('vendor', 'Vendor'),
        ('compliance', 'Compliance'),
        ('security', 'Security'),
    ], string="Risk Category")

    risk_scope = fields.Selection([
        ('project', 'Project'),
        ('epic', 'Epic'),
        ('story', 'Story'),
        ('task', 'Task'),
    ], string="Risk Scope")

    linked_item_ref = fields.Char(string="Linked Item")

    probability = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Probability")

    impact = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string="Impact")

    risk_score = fields.Integer(
        string="Risk Score",
        compute="_compute_risk_score",
        store=True
    )

    risk_severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string="Risk Severity",
       compute="_compute_risk_severity",
       store=True
    )

    risk_status = fields.Selection([
        ('open', 'Open'),
        ('monitoring', 'Monitoring'),
        ('mitigated', 'Mitigated'),
        ('closed', 'Closed'),
    ], string="Risk Status",
       default='open',
       tracking=True
    )

    risk_identified_date = fields.Date(string="Risk Identified Date")

    risk_expected_window = fields.Selection([
        ('immediate', 'Immediate'),
        ('short', 'Short-term'),
        ('long', 'Long-term'),
    ], string="Risk Expected Window")

    review_frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('sprint', 'Sprint'),
        ('monthly', 'Monthly'),
    ], string="Review Frequency")

    next_review_date = fields.Date(string="Next Review Date")

    # -----------------------
    # Compute Risk Score
    # -----------------------

    @api.depends('probability', 'impact')
    def _compute_risk_score(self):
        value_map = {
            'low': 1,
            'medium': 5,
            'high': 10,
        }
        for rec in self:
            prob = value_map.get(rec.probability, 0)
            imp = value_map.get(rec.impact, 0)
            rec.risk_score = prob * imp

    # -----------------------
    # Compute Risk Severity
    # -----------------------

    @api.depends('risk_score')
    def _compute_risk_severity(self):
        for rec in self:
            if rec.risk_score <= 1:
                rec.risk_severity = 'low'
            elif rec.risk_score <= 5:
                rec.risk_severity = 'medium'
            elif rec.risk_score <= 10:
                rec.risk_severity = 'high'
            else:
                rec.risk_severity = 'critical'
