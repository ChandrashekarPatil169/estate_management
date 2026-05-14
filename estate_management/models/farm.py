from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EstateSoilType(models.Model):
    _name = 'estate.soil.type'
    _description = 'Soil Type'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class EstateClimateZone(models.Model):
    _name = 'estate.climate.zone'
    _description = 'Climate Zone'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class EstateFarmType(models.Model):
    _name = 'estate.farm.type'
    _description = 'Farm Type'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class EstateFarm(models.Model):
    _name = 'estate.farm'
    _description = 'Farm'
    _inherit = ['mail.thread', 'estate.hierarchy.mixin', 'delete.notification.mixin']
    _rec_name = 'name'
    _order = "id desc"

    # Basic Info
    name = fields.Char(string="Farm Name", required=True, tracking=True)
    code = fields.Char(string="Farm Code / ID", tracking=True)  # Previously mismatched in XML
    code_locked = fields.Boolean(default=False, tracking=True)
    location = fields.Char(string="Location", tracking=True)
    hup_location_id = fields.Many2one(
        'estate.location',
        required=True,
        string="Location"
        , tracking=True
    )
    total_area = fields.Float(string="Total Area (acres/hectares)", tracking=True)
    soil_type = fields.Selection([
        ('loamy', 'Loamy'),
        ('clay', 'Clay'),
        ('sandy', 'Sandy'),
        ('other', 'Other')
    ], string="Soil Type", tracking=True)
    climate_zone = fields.Selection([
        ('zone1', 'Zone 1'),
        ('zone2', 'Zone 2'),
        ('zone3', 'Zone 3')
    ], string="Climate Zone", tracking=True)
    farm_type = fields.Selection([
        ('coffee', 'Coffee'),
        ('tea', 'Tea'),
        ('cardamom', 'Cardamom'),
        ('coconut', 'Coconut'),
        ('mixed', 'Mixed')
    ], string="Farm Type", tracking=True)
    soil_type_id = fields.Many2one(
        'estate.soil.type',
        string="Soil Type",
        tracking=True
    )

    climate_zone_id = fields.Many2one(
        'estate.climate.zone',
        string="Climate Zone",
        tracking=True
    )

    farm_type_id = fields.Many2one(
        'estate.farm.type',
        string="Farm Type",
        tracking=True
    )
    owner_id = fields.Many2one(
        'res.partner',
        string="Owner",
        domain="[('is_company','=',True)]",
        tracking=True
    )
    manager_id = fields.Many2one('hr.employee', string="Manager")

    # Legal / Ownership
    ownership_type = fields.Selection([
        ('company', 'Company'),
        ('individual', 'Individual')
    ], string="Ownership Type", tracking=True)
    registration_number = fields.Char(string="Registration / License Number", tracking=True)
    start_date = fields.Date(string="Start Date", tracking=True)
    notes = fields.Text(string="Notes", tracking=True)

    # Relations
    property_id = fields.Many2one('estate.property', string="Properties", tracking=True)
    crop_ids = fields.One2many('estate.crop.name', 'farm_id', string="Crops", tracking=True)
    livestock_ids = fields.One2many('estate.livestock', 'farm_id', string="Livestock", tracking=True)
    farm_task_ids = fields.One2many('estate.farm.task', 'farm_id', string="Tasks", tracking=True)
    employee_ids = fields.Many2many('hr.employee', string="Employees", tracking=True)
    asset_ids = fields.One2many('estate.asset', 'assigned_farm_id', string="Assets", tracking=True)
    farm_plot_ids = fields.One2many('estate.farm.plot', 'farm_id', string="Plots", tracking=True)
    irrigation_ids = fields.One2many('estate.irrigation', 'farm_id', string="Irrigation Logs", tracking=True)
    compliance_ids = fields.One2many('estate.farm.compliance', 'farm_id', string="Compliance", tracking=True)
    sales_ids = fields.One2many('estate.farm.sales', 'farm_id', string="Post-Harvest & Sales", tracking=True)
    hup_property_id = fields.Many2one(
        'estate.property',
        string="Property",
        tracking=True
    )
    subfarm_ids = fields.Many2many(
        'estate.sub.farm',
        'estate_farm_subfarm_rel',
        'farm_id',
        'subfarm_id',
        string="Sub Farms"
        , tracking=True
    )

    subfarm_count = fields.Integer(
        compute='_compute_subfarm_count',
        string="Sub Farms"
        , tracking=True
    )

    def haction_open_subfarms(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub Farms',
            'res_model': 'estate.sub.farm',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.subfarm_ids.ids)],
            'context': {
                'default_farm_id': self.id,
                'default_property_id': self.hup_property_id.id or False,
                'default_hup_location_id': self.hup_location_id.id or False,
            }
        }

    def _compute_subfarm_count(self):
        for rec in self:
            rec.subfarm_count = len(rec.subfarm_ids)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            # 🔒 lock code
            if record.code:
                record.code_locked = True

            # 🔗 hierarchy sync ONLY using hup_property_id
            if record.hup_property_id:
                record._add_to_parent(
                    record.hup_property_id,
                    'hdown_farm_ids'
                )

        return records

    def write(self, vals):
        if 'code' in vals:
            for rec in self:
                if rec.code_locked:
                    raise ValidationError(_("Farm Code cannot be changed once saved."))

        res = super().write(vals)

        if 'code' in vals:
            self.filtered(lambda r: r.code and not r.code_locked).write({
                'code_locked': True
            })
        return res


class EstateWell(models.Model):
    _name = 'estate.well'
    _description = 'Well'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(string="Well Name", required=True, tracking=True)
    code = fields.Char(string="Well Code", tracking=True)
    location = fields.Char(string="Location", tracking=True)
    capacity = fields.Float(string="Water Capacity", tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class EstatePest(models.Model):
    _name = 'estate.pest'
    _description = 'Pest Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(string="Pest Name", required=True, tracking=True)
    code = fields.Char(string="Pest Code", tracking=True)
    category = fields.Selection(
        [
            ('insect', 'Insect'),
            ('fungus', 'Fungus'),
            ('weed', 'Weed'),
            ('bacteria', 'Bacteria'),
            ('other', 'Other')
        ],
        string="Category", tracking=True
    )
    severity = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        string="Severity", tracking=True
    )
    notes = fields.Text(string="Notes", tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class EstateMotorPump(models.Model):
    _name = 'estate.motor.pump'
    _description = 'Motor Pump'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(string="Motor Pump Name", required=True, tracking=True)
    code = fields.Char(string="Pump Code", tracking=True)
    power_rating = fields.Char(string="Power Rating", tracking=True)
    pump_type = fields.Selection(
        [
            ('electric', 'Electric'),
            ('diesel', 'Diesel'),
            ('solar', 'Solar')
        ],
        string="Pump Type", tracking=True
    )
    active = fields.Boolean(default=True, tracking=True)


class EstateChemicalType(models.Model):
    _name = 'estate.chemical.type'
    _description = 'Chemical Type Master'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(string="Chemical Type", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    description = fields.Text(string="Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)


class EstateCycleType(models.Model):
    _name = 'estate.cycle.type'
    _description = 'Cycle Type'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    description = fields.Text(tracking=True)


class EstateDisease(models.Model):
    _name = 'estate.disease'
    _description = 'Disease'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    severity = fields.Selection(
        [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]
        , tracking=True
    )
    notes = fields.Text(tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    crop_name_id = fields.Many2one(
        'estate.crop.name',
        string="Crop",
        required=True,
        ondelete='cascade'
        , tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.crop_name_id:
                rec.crop_name_id.write({
                    'disease_ids': [(4, rec.id)]
                })

        return records


class EstateFertilizer(models.Model):
    _name = 'estate.fertilizer'
    _description = 'Fertilizer'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True)
    code = fields.Char(tracking=True)
    fertilizer_type = fields.Selection(
        [('organic', 'Organic'), ('chemical', 'Chemical')]
        , tracking=True
    )
    active = fields.Boolean(default=True, tracking=True)
    subfarm_id = fields.Many2one(
        'estate.sub.farm',
        string="Sub Farm"
        , tracking=True
    )
    to_be_fertilized_date = fields.Date(string="To Be Fertilized Date", tracking=True)
    fertilized_date = fields.Date(string="Fertilized Date", tracking=True)
    reason = fields.Text(string="Reason", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.subfarm_id:
                rec.subfarm_id.write({
                    'fertilizer_ids': [(4, rec.id)]
                })

        return records


class EstateChemical(models.Model):
    _name = 'estate.chemical'
    _description = 'Chemical'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    purpose = fields.Char(string="Purpose", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    subfarm_id = fields.Many2one(
        'estate.sub.farm',
        string="Sub Farm"
        , tracking=True
    )

    to_be_used_date = fields.Date(string="To Be Used On", tracking=True)
    used_date = fields.Date(string="Chemical Used On Date", tracking=True)

    quantity = fields.Float(string="Quantity", tracking=True)

    pest_id = fields.Many2one(
        'estate.pest',
        string="Pest", tracking=True
    )
    chemical_type_id = fields.Many2one(
        'estate.chemical.type',
        string="Chemical Type", tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.subfarm_id:
                rec.subfarm_id.write({
                    'chemical_ids': [(4, rec.id)]
                })

        return records


class EstateWorker(models.Model):
    _inherit = 'res.partner'
    _order = "id desc"
    # _inherit = ['mail.thread', 'mail.activity.mixin',  'estate.security.mixin']

    subfarm_id = fields.Many2one(
        'estate.sub.farm',
        string="Sub Farm", tracking=True
    )

    crop_name_id = fields.Many2one(
        'estate.crop.name',
        related='subfarm_id.crop_name_id',
        store=True,
        readonly=True, tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if rec.subfarm_id:
                rec.subfarm_id.write({
                    'worker_ids': [(4, rec.id)]
                })

        return records


class EstateSubFarmHarvest(models.Model):
    _name = 'estate.subfarm.harvest'
    _description = 'SubFarm Harvest'
    _rec_name = 'harvested_date'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin']

    subfarm_id = fields.Many2one(
        'estate.sub.farm',
        string="Sub Farm",
        ondelete='cascade', tracking=True
    )

    planted_date = fields.Date(string="Planted Date", tracking=True)
    planted_quantity = fields.Float(string="Planted Quantity", tracking=True)

    expected_harvest_date = fields.Date(string="Expected Harvest Date", tracking=True)
    harvested_date = fields.Date(string="Harvested Date", tracking=True)

    harvested_quantity = fields.Float(string="Harvested Quantity", tracking=True)

    # 18/3/2026
    uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        related='harvest_product_id.uom_id',
        store=True,
        readonly=True,
        tracking=True
    )
    # uom_id = fields.Many2one(
    #     'uom.uom',
    #     string="Unit of Measure",tracking=True
    # )
    crop_name_id = fields.Many2one(
        'estate.crop.name',
        string="Crop Name", tracking=True
    )
    harvest_product_id = fields.Many2one(
        'estate.harvest.product',
        string="Harvest Product",
        tracking=True
    )

    # @api.model_create_multi
    # def create(self, vals_list):
    #
    #     records = super().create(vals_list)
    #
    #     for rec in records:
    #         if rec.subfarm_id:
    #             for subfarm in rec.subfarm_id:
    #                 subfarm.write({
    #                     'harvest_ids': [(4, rec.id)]
    #                 })
    #
    #     return records


class EstateSubFarm(models.Model):
    _name = 'estate.sub.farm'
    _description = 'Sub Farm'
    # _rec_name = 'subfarm_id'
    _rec_name = 'name'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'estate.security.mixin', 'delete.notification.mixin']

    name = fields.Char(string="Sub Farm Name", tracking=True, compute="_compute_name")
    code = fields.Char(string="Sub Farm Code", tracking=True)
    crop_variety = fields.Char(string="Crop Variety", tracking=True)

    farm_id_main = fields.Many2one(
        'estate.farm',
        string="Parent Farm",
        ondelete='cascade', tracking=True
    )

    area = fields.Float(string="Area", tracking=True)
    manager_id = fields.Many2one('res.users', string="Manager", tracking=True)
    notes = fields.Text(string="Notes", tracking=True)

    crop_name_id = fields.Many2one(
        'estate.crop.name',
        string="Crop Name",
        required=True
        , tracking=True
    )
    crop_code = fields.Char(string="Crop Code", tracking=True)
    batch_id = fields.Char(string="Batch ID", tracking=True)
    farm_id = fields.Many2one(
        'estate.farm',
        string="Farm",
        required=True,
        ondelete='cascade', tracking=True
    )
    harvested_quantity = fields.Float(string="Harvested Quantity", tracking=True)

    # -------------------------
    # DATES & QUANTITY
    # -------------------------
    planted_date = fields.Date(string="Planted Date", tracking=True)
    planted_quantity = fields.Float(string="Planted Quantity", tracking=True)

    expected_harvest_date = fields.Date(string="Expected Date of Harvest", tracking=True)
    harvested_date = fields.Date(string="Harvested Date", tracking=True)

    # -------------------------
    # SIZE WITH UOM
    # -------------------------
    subfarm_size = fields.Float(string="Subfarm Size", tracking=True)
    subfarm_uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure"
        , tracking=True
    )
    subfarm_id = fields.Char(
        string="SubFarm Name", tracking=True, required=True,
    )

    # -------------------------
    # OPERATIONS
    # -------------------------
    team_leader_id = fields.Many2one(
        'res.partner',
        string="Team Leader", tracking=True
    )

    cycle_type_id = fields.Many2one(
        'estate.cycle.type',
        string="Cycle Type", tracking=True
    )

    irrigation_required = fields.Boolean(string="Irrigation Required", tracking=True)

    well_id = fields.Many2one(
        'estate.well',
        string="Well", tracking=True
    )
    motor_pump_id = fields.Many2one(
        'estate.motor.pump',
        string="Motor Pump", tracking=True
    )

    # -------------------------
    # HEALTH & INPUTS (M2M)
    # -------------------------
    disease_ids = fields.Many2many(
        'estate.disease',
        string="Diseases", tracking=True
    )
    fertilizer_ids = fields.Many2many(
        'estate.fertilizer',
        string="Fertilizers", tracking=True
    )
    chemical_ids = fields.Many2many(
        'estate.chemical',
        string="Chemicals", tracking=True
    )
    worker_ids = fields.Many2many(
        'res.partner',
        string="Workers", tracking=True
    )

    # -------------------------
    # SMART BUTTON COUNTS
    # -------------------------
    disease_count = fields.Integer(
        compute="_compute_counts",
        string="Diseases", tracking=True
    )
    fertilizer_count = fields.Integer(
        compute="_compute_counts",
        string="Fertilizers", tracking=True
    )
    chemical_count = fields.Integer(
        compute="_compute_counts",
        string="Chemicals", tracking=True
    )
    worker_count = fields.Integer(
        compute="_compute_counts",
        string="Workers", tracking=True
    )
    crop_variety_id = fields.Many2one(
        'estate.crop.variety',
        string="Crop Variety", tracking=True
    )
    disease_id_main = fields.Many2many(
        'estate.disease',
        'estate_subfarm_disease_rel',
        'subfarm_id',
        'disease_id',
        string="Diseases Main", tracking=True
    )
    disease_text = fields.Text(string="Diseases", tracking=True)
    harvest_ids = fields.Many2many(
        'estate.subfarm.harvest',
        'estate_subfarm_harvest_rel',
        'subfarm_id',
        'harvest_id',
        string="Harvest Logs", tracking=True
    )
    harvest_count = fields.Float(
        compute="_compute_counts",
        string="Harvests", tracking=True
    )

    hcount_disease = fields.Integer(compute="_compute_counts", string="Diseases", tracking=True)
    hcount_fertilizer = fields.Integer(compute="_compute_counts", string="Fertilizers", tracking=True)
    hcount_chemical = fields.Integer(compute="_compute_counts", string="Chemicals", tracking=True)
    hcount_worker = fields.Integer(compute="_compute_counts", string="Workers", tracking=True)
    allowed_variety_ids = fields.Many2many(
        'estate.crop.variety',
        compute="_compute_allowed_varieties",
        string="Allowed Varieties", tracking=True
    )
    livestock_ids = fields.Many2many(
        'estate.livestock',
        'estate_subfarm_livestock_rel',
        'subfarm_id',
        'livestock_id',
        string="Livestock", tracking=True
    )
    hup_location_id = fields.Many2one(
        'estate.location',
        required=True,
        string="Location", tracking=True
    )
    livestock_count = fields.Integer(
        compute="_compute_counts",
        string="Livestock", tracking=True
    )
    property_id = fields.Many2one(
        'estate.property',
        string="Property",
        tracking=True
    )

    building_id = fields.Many2one(
        'estate.building',
        string="Building",
        tracking=True,
        domain="[('hup_property_id','=',property_id)]"
    )
    allowed_disease_ids = fields.Many2many(
        'estate.disease',
        compute='_compute_allowed_inputs',
        string="Allowed Diseases"
    )
    allowed_fertilizer_ids = fields.Many2many(
        'estate.fertilizer',
        'estate_subfarm_allowed_fertilizer_rel',
        'subfarm_id',
        'fertilizer_id',
        compute='_compute_allowed_inputs',
        string="Allowed Fertilizers"
    )

    allowed_chemical_ids = fields.Many2many(
        'estate.chemical',
        'estate_subfarm_allowed_chemical_rel',
        'subfarm_id',
        'chemical_id',
        compute='_compute_allowed_inputs',
        string="Allowed Chemicals"
    )

    @api.depends('crop_name_id')
    def _compute_allowed_inputs(self):
        for rec in self:
            if rec.crop_name_id:
                rec.allowed_fertilizer_ids = rec.crop_name_id.fertilizer_ids
                rec.allowed_chemical_ids = rec.crop_name_id.chemical_ids
                rec.allowed_disease_ids = rec.crop_name_id.disease_ids
            else:
                rec.allowed_fertilizer_ids = False
                rec.allowed_chemical_ids = False
                rec.allowed_disease_ids = False

    # @api.depends('crop_name_id')
    # def _compute_allowed_inputs(self):
    #     for rec in self:
    #         if rec.crop_name_id:
    #             rec.allowed_fertilizer_ids = rec.crop_name_id.fertilizer_ids
    #             rec.allowed_chemical_ids = rec.crop_name_id.chemical_ids
    #             rec.allowed_disease_ids = rec.crop_name_id.disease_ids
    #         else:
    #             rec.allowed_fertilizer_ids = [(5, 0, 0)]
    #             rec.allowed_chemical_ids = [(5, 0, 0)]
    #             rec.allowed_disease_ids = [(5, 0, 0)]

    @api.depends('crop_name_id')
    def _compute_allowed_varieties(self):
        for rec in self:
            if rec.crop_name_id:
                rec.allowed_variety_ids = rec.crop_name_id.variety_ids
            else:
                rec.allowed_variety_ids = [(5, 0, 0)]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('farm_id'):
                default_farm_id = self.env.context.get('default_farm_id')
                if default_farm_id:
                    vals['farm_id'] = default_farm_id

        records = super().create(vals_list)

        # ensure M2M link is also written
        for rec in records:
            rec.farm_id.write({
                'subfarm_ids': [(4, rec.id)]
            })

        return records

    # def haction_open_harvests(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Harvest Logs',
    #         'res_model': 'estate.subfarm.harvest',
    #         'view_mode': 'list,form',
    #         'domain': [('id', 'in', self.harvest_ids.ids)],
    #         'context': {
    #             'default_subfarm_id': self.id,
    #             'default_crop_name_id': self.crop_name_id.id,
    #         }
    #     }
    def haction_open_harvests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Harvest Logs',
            'res_model': 'estate.subfarm.harvest',
            'view_mode': 'list,form',
            'domain': [('subfarm_id', '=', self.id)],
            'context': {
                'default_subfarm_id': self.id,
                'default_crop_name_id': self.crop_name_id.id,
            }
        }

    def haction_open_diseases(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Diseases',
            'res_model': 'estate.disease',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.disease_ids.ids)],
        }

    def haction_open_fertilizers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fertilizers',
            'res_model': 'estate.fertilizer',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.fertilizer_ids.ids)],
            'context': {
                'default_subfarm_id': self.id,
            }
        }

    def haction_open_chemicals(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chemicals',
            'res_model': 'estate.chemical',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.chemical_ids.ids)],
            'context': {
                'default_subfarm_id': self.id,
            }
        }

    def haction_open_workers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Workers',
            'res_model': 'res.partner',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.worker_ids.ids)],
            'context': {
                'default_subfarm_id': self.id,
            }
        }

    def haction_open_livestock(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Livestock',
            'res_model': 'estate.livestock',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.livestock_ids.ids)],
            'context': {
                'default_subfarm_id': self.id,
                'default_farm_id': self.farm_id.id,
                'default_property_id': self.property_id.id or False,
                'default_building_id': self.building_id.id or False,
            }
        }

    @api.depends(
        'disease_ids',
        'fertilizer_ids',
        'chemical_ids',
        'worker_ids',
        'livestock_ids',
        'harvest_ids.harvested_quantity'
    )
    def _compute_counts(self):
        for rec in self:
            rec.disease_count = len(rec.disease_ids or [])
            rec.fertilizer_count = len(rec.fertilizer_ids or [])
            rec.chemical_count = len(rec.chemical_ids or [])
            rec.worker_count = len(rec.worker_ids or [])

            rec.hcount_disease = len(rec.disease_ids or [])
            rec.hcount_fertilizer = len(rec.fertilizer_ids or [])
            rec.hcount_chemical = len(rec.chemical_ids or [])
            rec.hcount_worker = len(rec.worker_ids or [])
            rec.livestock_count = len(rec.livestock_ids or [])
            harvests = self.env['estate.subfarm.harvest'].search([
                ('subfarm_id', '=', rec.id)
            ])

            rec.harvest_count = sum(harvests.mapped('harvested_quantity'))

    @api.depends('subfarm_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.subfarm_id
