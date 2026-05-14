from odoo import models, fields,api, _
from odoo.exceptions import ValidationError


class EstateAssetType(models.Model):
    _name = 'estate.asset.type'
    _description = 'Asset Type'
    _order = "name"

    name = fields.Char(string="Asset Type", required=True)
    code = fields.Char(string="Code")
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)


class EstateAsset(models.Model):
    _name = 'estate.asset'
    _description = 'Farm Asset'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(string="Asset Name", required=True, tracking=True)
    asset_type = fields.Selection([
        ('tractor','Tractor'),
        ('pump','Irrigation Pump'),
        ('vehicle','Vehicle'),
        ('tool','Tool'),
        ('other','Other')
    ], tracking=True)
    asset_type_id = fields.Many2one(
        'estate.asset.type',
        string="Asset Type",
        tracking=True
    )
    purchase_date = fields.Date(tracking=True)
    condition = fields.Selection([
        ('new','New'),
        ('good','Good'),
        ('used','Used'),
        ('needs_repair','Needs Repair')
    ], tracking=True)
    assigned_farm_id = fields.Many2one('estate.farm', string="Assigned Farm", tracking=True)
    assigned_plot_id = fields.Many2one('estate.farm.plot', string="Assigned Plot", tracking=True)
    assigned_task_id = fields.Many2one('estate.farm.task', string="Assigned Task", tracking=True)
    maintenance_logs = fields.Text(tracking=True)
    fuel_consumables = fields.Text(tracking=True)
    depreciation_info = fields.Text(tracking=True)
    code = fields.Char(string="Asset Code", tracking=True)
    code_locked = fields.Boolean(default=False, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            if vals.get('code'):
                record.code_locked = True
        return records

    def write(self, vals):
        if 'code' in vals:
            for rec in self:
                if rec.code_locked:
                    raise ValidationError(_("Asset Code cannot be changed once saved."))

        res = super().write(vals)

        if 'code' in vals:
            self.filtered(lambda r: r.code and not r.code_locked).write({
                'code_locked': True
            })
        return res

