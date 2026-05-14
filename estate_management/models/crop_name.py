# -*- coding: utf-8 -*-
from odoo import models, fields,api,_

class EstateCropMaster(models.Model):
    _name = 'estate.crop.master'
    _description = 'Crop Master'
    _order = "id desc"
    _inherit = ['mail.thread']

    name = fields.Char(string="Crop Name", required=True,tracking=True)

class EstateCropVariety(models.Model):
    _name = 'estate.crop.variety'
    _description = 'Crop Variety'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)

    crop_ids = fields.Many2many(
        'estate.crop.name',
        'estate_crop_variety_rel',
        'variety_id',
        'crop_id',
        string="Crops"
        , tracking=True
    )
    crop_name_id = fields.Many2one(
        'estate.crop.name',
        string="Crop",
        ondelete='cascade'
        , tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.crop_name_id:
                rec.crop_name_id.write({
                    'variety_ids': [(4, rec.id)]
                })

        return records


class EstateCropName(models.Model):
    _name = 'estate.crop.name'
    _description = 'Crop Name Master'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Many2one('estate.crop.master', string="Crop Name", required=True,tracking=True)

    variety = fields.Char(string="Variety", tracking=True)
    code = fields.Char(string="Crop Code / Batch ID", tracking=True)
    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    planting_date = fields.Date(string="Planting Date", tracking=True)
    expected_harvest_date = fields.Date(string="Expected Harvest Date", tracking=True)
    actual_harvest_date = fields.Date(string="Actual Harvest Date", tracking=True)

    cycle_type = fields.Selection(
        [('seasonal', 'Seasonal'), ('perennial', 'Perennial')],
        string="Cycle Type",
        tracking=True
    )
    well_id = fields.Many2one(
        'estate.well',
        string="Well",
        tracking=True
    )

    motor_pump_id = fields.Many2one(
        'estate.motor.pump',
        string="Motor Pump",
        tracking=True
    )

    area_cultivated = fields.Float(string="Area Cultivated", tracking=True)
    irrigation_required = fields.Boolean(string="Irrigation Required", tracking=True)
    expected_yield = fields.Float(string="Expected Yield", tracking=True)
    actual_yield = fields.Float(string="Actual Yield", tracking=True)

    quality_grade = fields.Selection(
        [('A', 'A'), ('B', 'B'), ('C', 'C')],
        string="Quality Grade",
        tracking=True
    )

    storage_location_id = fields.Many2one('estate.room', string="Storage Location", tracking=True)
    fertilizers_used = fields.Text(string="Fertilizers / Chemicals Used", tracking=True)
    disease_history = fields.Text(string="Disease / Pest History", tracking=True)
    notes = fields.Text(string="Notes", tracking=True)
    variety_ids = fields.Many2many(
        'estate.crop.variety',
        'estate_crop_variety_rel',
        'crop_id',
        'variety_id',
        string="Varieties"
        , tracking=True
    )

    disease_ids = fields.Many2many(
        'estate.disease',
        'estate_crop_disease_rel',
        'crop_id',
        'disease_id',
        string="Diseases"
        , tracking=True
    )
    variety_count = fields.Integer(
        compute='_compute_counts'
        , tracking=True
    )

    disease_count = fields.Integer(
        compute='_compute_counts'
        , tracking=True
    )
    fertilizer_ids = fields.Many2many(
        'estate.fertilizer',
        'estate_crop_fertilizer_rel',
        'crop_id',
        'fertilizer_id',
        string="Fertilizers"
    )

    chemical_ids = fields.Many2many(
        'estate.chemical',
        'estate_crop_chemical_rel',
        'crop_id',
        'chemical_id',
        string="Chemicals"
    )

    fertilizer_count = fields.Integer(
        compute='_compute_counts',
        string="Fertilizers"
    )

    chemical_count = fields.Integer(
        compute='_compute_counts',
        string="Chemicals"

    )

    def _compute_counts(self):
        for rec in self:
            rec.variety_count = len(rec.variety_ids)
            rec.disease_count = len(rec.disease_ids)
            rec.fertilizer_count = len(rec.fertilizer_ids)
            rec.chemical_count = len(rec.chemical_ids)   

    def haction_open_fertilizers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fertilizers',
            'res_model': 'estate.fertilizer',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.fertilizer_ids.ids)],
            'context': {
                'default_crop_name_id': self.id,
            }
        }

    def haction_open_chemicals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chemicals',
            'res_model': 'estate.chemical',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.chemical_ids.ids)],
            'context': {
                'default_crop_name_id': self.id,
            }
        }

    def haction_open_varieties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Varieties',
            'res_model': 'estate.crop.variety',
            'view_mode': 'list,form',
            'domain': [('crop_name_id', '=', self.id)],
            'context': {
                'default_crop_name_id': self.id,
            }
        }

    def haction_open_diseases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Diseases',
            'res_model': 'estate.disease',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.disease_ids.ids)],
            'context': {
                'default_crop_name_id': self.id,
            }
        }
