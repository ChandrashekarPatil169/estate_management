from odoo import models, fields

class ProgressConfig(models.Model):
    _name = "progress.config"
    _description = "Progress Color Config"

    name = fields.Char(required=True)

    line_ids = fields.One2many(
        "progress.config.line",
        "config_id",
        string="Progress Color Range",
        required=True
    )


class ProgressConfigLine(models.Model):
    _name = "progress.config.line"
    _description = "Progress Color Line"

    config_id = fields.Many2one(
        "progress.config",
        required=True,
        ondelete="cascade"
    )

    min_value = fields.Float("From %", required=True)
    max_value = fields.Float("To %", required=True)

    color = fields.Selection([
        ('bg-success', 'Green'),
        ('bg-warning', 'Yellow'),
        ('bg-danger', 'Red'),
        ('bg-info', 'Blue'),
        ('bg-primary', 'Purple'),
        ('bg-dark', 'Black'),
    ], string="Color", required=True)

    # color_code = fields.Char("Color")