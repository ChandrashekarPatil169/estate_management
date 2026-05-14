from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EstateLivestock(models.Model):
    _name = 'estate.livestock'
    _description = 'Livestock'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin','delete.notification.mixin']  # Enable chatter & followers
    _rec_name = 'animal_config_id'
    _order = "id desc"
    # Basic Info
    animal_type = fields.Selection([
        ('cow', 'Cow'),
        ('goat', 'Goat'),
        ('hen', 'Hen'),
        ('other', 'Other')
    ], string="Animal Type", tracking=True)
    breed = fields.Char(tracking=True)
    group_name = fields.Char(tracking=True)
    farm_id = fields.Many2one('estate.farm', string="Farm", tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ],tracking=True)
    # Counts
    total_count = fields.Integer(tracking=True)
    male_count = fields.Integer(tracking=True)
    female_count = fields.Integer(tracking=True)
    birth_date = fields.Date(tracking=True)

    # Production
    milk_production = fields.Float(tracking=True)
    egg_production = fields.Float(tracking=True)
    meat_production = fields.Float(tracking=True)

    # Health Records
    vaccination_records = fields.Text(tracking=True)
    medical_treatments = fields.Text(tracking=True)
    diseases = fields.Text(tracking=True)

    # Housing
    building_id_main = fields.Many2one('estate.building',tracking=True)
    floor_id = fields.Many2one('estate.floor',tracking=True)
    unit_id = fields.Many2one('estate.unit',tracking=True)
    room_id = fields.Many2one('estate.room',tracking=True)

    # Additional Fields for Form View
    breeding_records = fields.Text(string="Breeding Records",tracking=True)
    feed_management = fields.Text(string="Feed Management",tracking=True)
    pedigree = fields.Text(string="Pedigree",tracking=True)

    code = fields.Char(string="Livestock Code", tracking=True)
    code_locked = fields.Boolean(default=False,tracking=True)
    animal_config_id = fields.Many2one(
        'estate.livestock.sub',
        string="Animal Type",
        required=True
        , tracking=True
    )

    breed_ids = fields.Many2many(
        'estate.breed',
        string="Breeds"
        , tracking=True
    )

    feed_ids = fields.Many2many(
        'estate.feed',
        string="Feed"
        , tracking=True
    )

    disease_ids = fields.Many2many(
        'estate.livestock.disease',
        string="Diseases"

    )
    property_id = fields.Many2one(
        'estate.property',
        string="Property",
        tracking=True
    )

    building_id= fields.Many2one(
        'estate.building',
        string="Building",
        tracking=True,
        domain="[('hup_property_id','=',property_id)]"
    )
    unique_id = fields.Char(
        string="Unique ID",
        copy=False,
        index=True
        , tracking=True
    )
    subfarm_ids = fields.Many2many(
        'estate.sub.farm',
        'estate_subfarm_livestock_rel',
        'livestock_id',
        'subfarm_id',
        string="Sub Farms"
        , tracking=True
    )
    subfarm_id = fields.Many2one(
        'estate.sub.farm',
        string="Sub Farm",
        ondelete='cascade',
        tracking=True
    )
    feeding_ids = fields.Many2many(
        'estate.livestock.feeding',
        'estate_livestock_feeding_rel',
        'livestock_id',
        'feeding_id',
        string="Feeding Logs"

    )

    medical_ids = fields.Many2many(
        'estate.livestock.medical',
        'estate_livestock_medical_rel',
        'livestock_id',
        'medical_id',
        string="Medical Logs"

    )

    harvest_ids = fields.Many2many(
        'estate.livestock.harvest',
        'estate_livestock_harvest_rel',
        'livestock_id',
        'harvest_id',
        string="Harvest Logs",
        tracking=True
    )
    feeding_count = fields.Integer(compute="_compute_log_counts",tracking=True)
    medical_count = fields.Integer(compute="_compute_log_counts",tracking=True)
    harvest_count = fields.Integer(compute="_compute_log_counts",tracking=True)
    allowed_breed_ids = fields.Many2many(
        'estate.breed',
        compute='_compute_allowed_domains',tracking=True
    )

    allowed_feed_ids = fields.Many2many(
        'estate.feed',
        compute='_compute_allowed_domains',tracking=True
    )

    allowed_disease_ids = fields.Many2many(
        'estate.livestock.disease',
        compute='_compute_allowed_domains',tracking=True
    )

    @api.depends('animal_config_id')
    def _compute_allowed_domains(self):
        for rec in self:
            if rec.animal_config_id:
                rec.allowed_breed_ids = rec.animal_config_id.breed_ids
                rec.allowed_feed_ids = rec.animal_config_id.feed_ids
                rec.allowed_disease_ids = rec.animal_config_id.disease_ids
            else:
                rec.allowed_breed_ids = [(5, 0, 0)]
                rec.allowed_feed_ids = [(5, 0, 0)]
                rec.allowed_disease_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        default_subfarm_id = self.env.context.get('default_subfarm_id')

        if default_subfarm_id:
            subfarm = self.env['estate.sub.farm'].browse(default_subfarm_id)
            for rec in records:
                subfarm.write({
                    'livestock_ids': [(4, rec.id)]
                })

        return records

    def write(self, vals):
        if 'code' in vals:
            for rec in self:
                if rec.code_locked:
                    raise ValidationError(_("Livestock Code cannot be changed once saved."))

        res = super().write(vals)

        if 'code' in vals:
            self.filtered(lambda r: r.code and not r.code_locked).write({
                'code_locked': True
            })
        return res



    @api.depends('feeding_ids', 'medical_ids', 'harvest_ids')
    def _compute_log_counts(self):
        for rec in self:
            rec.feeding_count = len(rec.feeding_ids)
            rec.medical_count = len(rec.medical_ids)
            rec.harvest_count = len(rec.harvest_ids)

    def action_open_feeding(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Feeding Logs',
            'res_model': 'estate.livestock.feeding',
            'view_mode': 'list,form',
            'domain': [('livestock_id', '=', self.id)],
            'context': {
                'default_livestock_id': self.id,
                'default_animal_type_id': self.animal_config_id.animal_type_id.id
            }
        }

    def action_open_medical(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Logs',
            'res_model': 'estate.livestock.medical',
            'view_mode': 'list,form',
            'domain': [('livestock_id', '=', self.id)],
            'context': {
                'default_livestock_id': self.id,
                'default_animal_type_id': self.animal_config_id.animal_type_id.id
            }
        }

    def action_open_harvest(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Harvest Logs',
            'res_model': 'estate.livestock.harvest',
            'view_mode': 'list,form',
            'domain': [('livestock_id', '=', self.id)],
            'context': {
                'default_livestock_id': self.id,
                'default_animal_type_id': self.animal_config_id.animal_type_id.id
            }
        }


class EstateAnimalType(models.Model):
    _name = 'estate.animal.type'
    _description = 'Animal Type Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    code = fields.Char(tracking=True)
    active = fields.Boolean(default=True,tracking=True)


class EstateBreed(models.Model):
    _name = 'estate.breed'
    _description = 'Breed Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    code = fields.Char(tracking=True)
    animal_type_id = fields.Many2one(
        'estate.animal.type',
        string="Animal Type",
        required=True,tracking=True
    )
    active = fields.Boolean(default=True,tracking=True)


class EstateLivestockDisease(models.Model):
    _name = 'estate.livestock.disease'
    _description = 'Livestock Disease Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ],tracking=True)
    notes = fields.Text(tracking=True)
    active = fields.Boolean(default=True,tracking=True)


class EstateHarvestProduct(models.Model):
    _name = 'estate.harvest.product'
    _description = 'Harvested Product Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    code = fields.Char(tracking=True)
    uom_id = fields.Many2one('uom.uom', string="UoM",tracking=True)
    active = fields.Boolean(default=True,tracking=True)


class EstateFeed(models.Model):
    _name = 'estate.feed'
    _description = 'Feed Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    feed_type = fields.Selection([
        ('dry', 'Dry'),
        ('wet', 'Wet'),
        ('mixed', 'Mixed')
    ],tracking=True)
    notes = fields.Text(tracking=True)
    active = fields.Boolean(default=True,tracking=True)


class EstateMedicalTreatment(models.Model):
    _name = 'estate.medical.treatment'
    _description = 'Medical Treatment Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    name = fields.Char(required=True,tracking=True)
    treatment_type = fields.Selection([
        ('vaccine', 'Vaccine'),
        ('medicine', 'Medicine'),
        ('surgery', 'Surgery'),
        ('other', 'Other')
    ],tracking=True)
    notes = fields.Text(tracking=True)
    active = fields.Boolean(default=True,tracking=True)


class EstateLivestocksub(models.Model):
    _name = 'estate.livestock.sub'
    _description = 'Livestock Master'
    _rec_name = 'animal_type_id'
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']
    _order = "id desc"

    tag_number = fields.Char(string="Tag Number",tracking=True)

    animal_type_id = fields.Many2one(
        'estate.animal.type',
        string="Animal Type",
        required=True,tracking=True
    )

    breed_ids = fields.Many2many(
        'estate.breed',
        'estate_livestock_breed_rel',
        'livestock_id',
        'breed_id',
        string="Breed",tracking=True
    )

    disease_ids = fields.Many2many(
        'estate.livestock.disease',
        'estate_livestock_disease_rel',
        'livestock_id',
        'disease_id',
        string="Diseases",tracking=True
    )

    harvest_product_ids = fields.Many2many(
        'estate.harvest.product',
        'estate_livestock_product_rel',
        'livestock_id',
        'product_id',
        string="Harvested Products",tracking=True
    )

    feed_ids = fields.Many2many(
        'estate.feed',
        'estate_livestock_feed_rel',
        'livestock_id',
        'feed_id',
        string="Feed",tracking=True
    )

    medical_treatment_ids = fields.Many2many(
        'estate.medical.treatment',
        'estate_livestock_treatment_rel',
        'livestock_id',
        'treatment_id',
        string="Medical Treatments"
    )

    birth_date = fields.Date(string="Birth Date",tracking=True)

    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ],tracking=True)

    active = fields.Boolean(default=True,tracking=True)



class EstateLivestockFeeding(models.Model):
    _name = 'estate.livestock.feeding'
    _description = 'Livestock Feeding'
    _rec_name = "feed_id"
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']


    livestock_id = fields.Many2one(
        'estate.livestock',
        string="Livestock",
        ondelete='cascade'
        , tracking=True
    )

    animal_type_id = fields.Many2one(
        'estate.animal.type',
        string="Animal Type",
        store=True
        , tracking=True
    )

    feed_type_id = fields.Many2one(
        'estate.feed',
        string="Feed Type",tracking=True
    )

    feed_id = fields.Many2one(
        'estate.feed',
        string="Feed",tracking=True
    )
    allowed_feed_ids = fields.Many2many(
        'estate.feed',
        string="Allowed Feeds",tracking=True
    )

    expected_feed_time = fields.Datetime(string="Expected Feed Time",tracking=True)
    actual_feed_time = fields.Datetime(string="Actual Feed Time",tracking=True)

    # @api.onchange('animal_type_id')
    # def _onchange_animal_type_id(self):
    #
    #     # Clear existing selections
    #     self.feed_id = False
    #     self.feed_type_id = False
    #
    #     if self.animal_type_id:
    #
    #         feeds = self.env['estate.feed'].search([
    #             ('animal_type_id', '=', self.animal_type_id.id)
    #         ])
    #
    #         # Store allowed values
    #         self.allowed_feed_ids = [(6, 0, feeds.ids)]
    #
    #     else:
    #         self.allowed_feed_ids = [(5, 0, 0)]

    @api.onchange('animal_type_id')
    def _onchange_animal_type_id(self):

        # Clear old selection
        self.feed_id = False
        self.feed_type_id = False

        if self.animal_type_id:

            configs = self.env['estate.livestock.sub'].search([
                ('animal_type_id', '=', self.animal_type_id.id)
            ])

            feeds = configs.mapped('feed_ids')

            self.allowed_feed_ids = [(6, 0, feeds.ids)]

        else:
            self.allowed_feed_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for rec in records:
            if rec.animal_type_id:

                livestock_records = self.env['estate.livestock'].search([
                    ('animal_config_id.animal_type_id', '=', rec.animal_type_id.id)
                ])

                for livestock in livestock_records:
                    livestock.write({
                        'feeding_ids': [(4, rec.id)]
                    })

        return records


class EstateLivestockMedical(models.Model):
    _name = 'estate.livestock.medical'
    _description = 'Livestock Medical Treatment'
    _inherit = ['mail.thread','mail.activity.mixin',  'estate.security.mixin']
    _rec_name = "disease_id"
    _order = "id desc"

    livestock_id = fields.Many2one(
        'estate.livestock',
        ondelete='cascade',tracking = True
    )

    animal_type_id = fields.Many2one(
        'estate.animal.type',
        store=True,tracking = True
    )

    medical_treatment_id = fields.Many2one(
        'estate.medical.treatment',
        string="Medical Treatment",tracking = True
    )
    medical_treatment_ids = fields.Many2many(
        'estate.medical.treatment',
        'estate_medical_treatment_rel',
        'medical_id',
        'treatment_id',
        string="Medical Treatments",tracking = True
    )

    treatment_date = fields.Datetime()
    allowed_medical_ids = fields.Many2many(
        'estate.medical.treatment',
        string="Allowed Medical Treatments",tracking = True
    )
    disease_ids = fields.Many2many(
        'estate.livestock.disease',
        'estate_medical_disease_rel',  # Explicit relation table
        'medical_id',
        'disease_id',
        string="Diseases",tracking = True
    )
    disease_id = fields.Many2one(
        'estate.livestock.disease',
        string="Disease",tracking = True
    )
    allowed_disease_ids = fields.Many2many(
        'estate.livestock.disease',
        compute='_compute_allowed_domains',
        store=False,tracking = True
    )

    def _compute_allowed_domains(self):
        for rec in self:
            if rec.animal_type_id:
                configs = self.env['estate.livestock.sub'].search([
                    ('animal_type_id', '=', rec.animal_type_id.id)
                ])

                rec.allowed_medical_ids = configs.mapped('medical_treatment_ids')
                rec.allowed_disease_ids = configs.mapped('disease_ids')
            else:
                rec.allowed_medical_ids = [(5, 0, 0)]
                rec.allowed_disease_ids = [(5, 0, 0)]

    @api.onchange('animal_type_id')
    def _onchange_animal_type_id(self):

        # Clear old selections
        self.medical_treatment_ids = [(5, 0, 0)]
        self.disease_id = False

        if self.animal_type_id:

            configs = self.env['estate.livestock.sub'].search([
                ('animal_type_id', '=', self.animal_type_id.id)
            ])

            treatments = configs.mapped('medical_treatment_ids')
            diseases = configs.mapped('disease_ids')

            # Store allowed values
            self.allowed_medical_ids = [(6, 0, treatments.ids)]
            self.allowed_disease_ids = [(6, 0, diseases.ids)]

        else:
            self.allowed_medical_ids = [(5, 0, 0)]
            self.allowed_disease_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for rec in records:
            if rec.animal_type_id:

                livestock_records = self.env['estate.livestock'].search([
                    ('animal_config_id.animal_type_id', '=', rec.animal_type_id.id)
                ])

                for livestock in livestock_records:
                    livestock.write({
                        'medical_ids': [(4, rec.id)]
                    })

        return records


class EstateLivestockHarvest(models.Model):
    _name = 'estate.livestock.harvest'
    _description = 'Livestock Harvest'
    _rec_name = "harvest_product_id"


    livestock_id = fields.Many2one(
        'estate.livestock',
        ondelete='cascade',tracking=True
    )

    animal_type_id = fields.Many2one(
        'estate.animal.type',
        store=True,tracking=True
    )

    harvest_product_id = fields.Many2one(
        'estate.harvest.product',
        string="Harvest Product",tracking=True,domain="[('id','in', allowed_product_ids)]"
    )
    allowed_product_ids = fields.Many2many(
        'estate.harvest.product',
        compute="_compute_allowed_products",
        string="Allowed Products",
        store=False
    )
    expected_harvest_date = fields.Datetime(tracking=True)
    actual_harvest_datetime = fields.Datetime(tracking=True)
    harvested_quantity = fields.Float(tracking=True)
    # 18/3/2026
    uom_id = fields.Many2one(
        'uom.uom',
        string="UoM",
        related='harvest_product_id.uom_id',
        store=True,
        readonly=True,
        tracking=True
    )
    # uom_id = fields.Many2one('uom.uom', string="UoM",tracking=True)

    @api.depends('animal_type_id')
    def _compute_allowed_products(self):
        for rec in self:
            if rec.animal_type_id:

                configs = self.env['estate.livestock.sub'].search([
                    ('animal_type_id', '=', rec.animal_type_id.id)
                ])

                rec.allowed_product_ids = configs.mapped('harvest_product_ids')

            else:
                rec.allowed_product_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        for rec in records:
            if rec.animal_type_id:

                livestock_records = self.env['estate.livestock'].search([
                    ('animal_config_id.animal_type_id', '=', rec.animal_type_id.id)
                ])

                for livestock in livestock_records:
                    livestock.write({
                        'harvest_ids': [(4, rec.id)]
                    })

        return records




