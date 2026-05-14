from odoo import models, fields, api
from odoo.exceptions import ValidationError


class InventoryModelMaster(models.Model):
    _name = 'inventory.model.master'
    _description = 'Inventory Model Master'
    _rec_name = 'model_id'
    _inherit = ['mail.thread']
    _order = "id desc"

    asset_type_id = fields.Many2one('inventory.asset.type', string='Asset Type')

    asset_category_id = fields.Many2one(
        'inventory.asset.category',
        string='Asset Category',
        required=True
    )

    product_name_id = fields.Many2one(
        'inventory.product',
        string='Product Name',
        required=True
    )

    brand_id = fields.Many2one(
        'inventory.brand',
        string='Brand',
        required=True
    )

    model_id = fields.Many2one(
        'inventory.model',
        string='Model',
        required=True
    )

    # warehouse_id = fields.Many2one(
    #     'inventory.warehouse',
    #     string="Warehouse",
    #     tracking=True,
    #     domain=lambda self: [
    #         ('id', 'in',
    #          self.env.user.warehouse_exec_ids.ids +
    #          self.env.user.warehouse_manager_ids.ids)
    #     ]
    # )
    allowed_warehouse_ids = fields.Many2many(
        'inventory.warehouse',
        compute='_compute_allowed_warehouses'
    )

    # 2. Update your actual warehouse field to use the helper
    warehouse_id = fields.Many2one(
        'inventory.warehouse',
        string='Warehouse',
        domain="[('id', 'in', allowed_warehouse_ids)]"
    )

    @api.depends_context('uid')
    def _compute_allowed_warehouses(self):
        for rec in self:
            user = self.env.user
            # Combine the IDs from both roles
            allowed_ids = user.warehouse_exec_ids.ids + user.warehouse_manager_ids.ids
            rec.allowed_warehouse_ids = [(6, 0, allowed_ids)]

    @api.constrains('warehouse_id')
    def _check_warehouse_access(self):
        for rec in self:
            user = rec.env.user

            is_exec = user.has_group('custom_inventory.group_warehouse_executive')
            is_manager = user.has_group('custom_inventory.group_warehouse_manager')

            exec_ids = user.warehouse_exec_ids.ids
            manager_ids = user.warehouse_manager_ids.ids

            # Decide allowed warehouses
            if is_exec and not is_manager:
                allowed_ids = exec_ids

            elif is_manager and not is_exec:
                allowed_ids = manager_ids

            elif is_exec and is_manager:
                allowed_ids = exec_ids + manager_ids

            else:
                allowed_ids = []

            # 🚨 VALIDATION
            if rec.warehouse_id and rec.warehouse_id.id not in allowed_ids:
                raise ValidationError(
                    "You are not allowed to select this warehouse based on your role."
                )


    # ================= CORE FIX (COMPUTE BASED) =================

    inventory_ids = fields.Many2many(
        'custom.inventory',
        compute='_compute_inventory_tabs',
        string='Inventory Items',
        search='_search_inventory_ids'
    )

    inventory_product_ids = fields.Many2many(
        'custom.inventory',
        compute='_compute_inventory_tabs',
        string="Inventory Products"
    )

    inventory_deployed_ids = fields.Many2many(
        'custom.inventory',
        compute='_compute_inventory_tabs',
        string="Deployed Products"
    )

    inventory_service_ids = fields.Many2many(
        'custom.inventory',
        compute='_compute_inventory_tabs',
        string="Service & Repair"
    )

    inventory_retired_ids = fields.Many2many(
        'custom.inventory',
        compute='_compute_inventory_tabs',
        string="Retired"
    )

    inventory_disposed_ids = fields.Many2many(
        'custom.inventory',
        compute='_compute_inventory_tabs',
        string="Disposed"
    )

    @api.depends('model_id', 'asset_type_id', 'warehouse_id')
    def _compute_inventory_tabs(self):
        for rec in self:
            domain = []

            if rec.model_id:
                domain.append(('model_id', '=', rec.model_id.id))

            if rec.asset_type_id:
                domain.append(('asset_type_id', '=', rec.asset_type_id.id))

            if rec.warehouse_id:
                domain.append(('warehouse_id', '=', rec.warehouse_id.id))

            all_records = self.env['custom.inventory'].search(domain)

            rec.inventory_ids = all_records
            rec.inventory_product_ids = all_records.filtered(lambda r: r.lifecycle_state == 'in_stock')
            rec.inventory_deployed_ids = all_records.filtered(lambda r: r.lifecycle_state == 'in_use')
            rec.inventory_service_ids = all_records.filtered(lambda r: r.lifecycle_state == 'maintenance')
            rec.inventory_retired_ids = all_records.filtered(lambda r: r.lifecycle_state == 'retired')
            rec.inventory_disposed_ids = all_records.filtered(lambda r: r.lifecycle_state == 'disposed')

    # ================= EXISTING LOGIC (UNCHANGED) =================

    total_serial_count = fields.Integer(string='Total Serial Numbers', store=False)

    floor_id = fields.Many2one('estate.floor', string="Floor")
    building_id = fields.Many2one('estate.building', string="Building")
    property_id = fields.Many2one('estate.property', string="Property")
    unit_id = fields.Many2one('estate.unit', string="Unit")
    room_id = fields.Many2one('estate.room', string="Room")

    allowed_asset_type_ids = fields.Many2many(
        'inventory.asset.type',
        compute='_compute_allowed_fields'
    )

    allowed_asset_category_ids = fields.Many2many(
        'inventory.asset.category',
        compute='_compute_allowed_fields'
    )

    allowed_product_ids = fields.Many2many(
        'inventory.product',
        compute='_compute_allowed_fields'
    )

    allowed_brand_ids = fields.Many2many(
        'inventory.brand',
        compute='_compute_allowed_fields'
    )

    total_count = fields.Integer(string="Total", compute="_compute_tab_counts",store=True)
    inventory_product_count = fields.Integer(string="Inventory Product", compute="_compute_tab_counts",store=True)
    deployed_count = fields.Integer(string="Deployed Products", compute="_compute_tab_counts",store=True)
    service_count = fields.Integer(string="Service & Repair Products", compute="_compute_tab_counts",store=True)
    retired_count = fields.Integer(string="Retired Products", compute="_compute_tab_counts",store=True)
    disposed_count = fields.Integer(string="Disposed Products", compute="_compute_tab_counts",store=True)

    def _validate_followers_against_warehouse(self, partners, vals=None):
        for record in self:

            warehouse = record.warehouse_id

            if vals and vals.get('warehouse_id'):
                warehouse = self.env['inventory.warehouse'].browse(vals['warehouse_id'])

            if not warehouse:
                continue

            for partner in partners:
                user = partner.user_ids[:1]

                if not user:
                    continue

                allowed_warehouses = (
                        user.warehouse_exec_ids.ids +
                        user.warehouse_manager_ids.ids
                )

                if warehouse.id not in allowed_warehouses:
                    raise ValidationError(
                        f"{user.name} is not assigned to warehouse '{warehouse.name}'."
                    )

    # @api.depends('model_id')
    # def _compute_tab_counts(self):
    #     for rec in self:
    #         if not rec.model_id:
    #             rec.total_count = 0
    #             rec.inventory_product_count = 0
    #             rec.deployed_count = 0
    #             rec.service_count = 0
    #             rec.retired_count = 0
    #             rec.disposed_count = 0
    #             continue
    #
    #         all_inventory = self.env['custom.inventory'].search([
    #             ('model_id', '=', rec.model_id.id)
    #         ])
    #
    #         rec.total_count = len(all_inventory)
    #         rec.inventory_product_count = len(all_inventory.filtered(lambda r: r.lifecycle_state == 'in_stock'))
    #         rec.deployed_count = len(all_inventory.filtered(lambda r: r.lifecycle_state == 'in_use'))
    #         rec.service_count = len(all_inventory.filtered(lambda r: r.lifecycle_state == 'maintenance'))
    #         rec.retired_count = len(all_inventory.filtered(lambda r: r.lifecycle_state == 'retired'))
    #         rec.disposed_count = len(all_inventory.filtered(lambda r: r.lifecycle_state == 'disposed'))

    # @api.depends('model_id', 'asset_type_id', 'warehouse_id')
    @api.depends('model_id','asset_type_id','warehouse_id','inventory_ids','inventory_ids.lifecycle_state')
    def _compute_tab_counts(self):
        for rec in self:

            domain = []

            if rec.model_id:
                domain.append(('model_id', '=', rec.model_id.id))

            if rec.asset_type_id:
                domain.append(('asset_type_id', '=', rec.asset_type_id.id))

            if rec.warehouse_id:
                domain.append(('warehouse_id', '=', rec.warehouse_id.id))

            # 🔥 SAME DATA SOURCE AS TABS
            all_records = self.env['custom.inventory'].search(domain)

            # 🔥 COUNTS EXACTLY MATCH TABS
            rec.total_count = len(all_records)

            rec.inventory_product_count = len(
                all_records.filtered(lambda r: r.lifecycle_state == 'in_stock')
            )

            rec.deployed_count = len(
                all_records.filtered(lambda r: r.lifecycle_state == 'in_use')
            )

            rec.service_count = len(
                all_records.filtered(lambda r: r.lifecycle_state == 'maintenance')
            )

            rec.retired_count = len(
                all_records.filtered(lambda r: r.lifecycle_state == 'retired')
            )

            rec.disposed_count = len(
                all_records.filtered(lambda r: r.lifecycle_state == 'disposed')
            )

    @api.depends('model_id')
    def _compute_allowed_fields(self):
        for rec in self:

            if not rec.model_id:
                rec.allowed_asset_type_ids = False
                rec.allowed_asset_category_ids = False
                rec.allowed_product_ids = False
                rec.allowed_brand_ids = False
                continue

            inventory_records = self.env['custom.inventory'].search([
                ('model_id', '=', rec.model_id.id)
            ])

            rec.allowed_asset_type_ids = inventory_records.mapped('asset_type_id')
            rec.allowed_asset_category_ids = inventory_records.mapped('asset_category_id')
            rec.allowed_product_ids = inventory_records.mapped('product_name_id')
            rec.allowed_brand_ids = inventory_records.mapped('brand_id')

    @api.onchange('model_id')
    def _onchange_model_fetch_product_brand(self):
        for rec in self:
            if rec.model_id:
                rec.product_name_id = rec.model_id.product_name_id
                rec.brand_id = rec.model_id.brand_id
            else:
                rec.product_name_id = False
                rec.brand_id = False

    def write(self, vals):

        if 'message_partner_ids' in vals:
            partner_ids = []

            for command in vals.get('message_partner_ids'):
                if command[0] == 4:
                    partner_ids.append(command[1])
                elif command[0] == 6:
                    partner_ids.extend(command[2])

            partners = self.env['res.partner'].browse(partner_ids)
            self._validate_followers_against_warehouse(partners, vals)

        return super().write(vals)

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        if partner_ids:
            partners = self.env['res.partner'].browse(partner_ids)
            self._validate_followers_against_warehouse(partners)

        return super().message_subscribe(
            partner_ids=partner_ids,
            subtype_ids=subtype_ids
        )

    def _search_inventory_ids(self, operator, value):
        # This tells Odoo: "When searching inventory_ids, search the model_id instead"
        return [('model_id', operator, value)]















# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
#
# class InventoryModelMaster(models.Model):
#     _name = 'inventory.model.master'
#     _description = 'Inventory Model Master'
#     _rec_name = 'model_id'
#     _inherit = ['mail.thread']
#
#     # warehouse_id = fields.Many2one(
#     #     'inventory.warehouse',  # ✅ KEEP THIS
#     #     string="Warehouse",
#     #     required=True
#     # )
#     asset_type_id = fields.Many2one(
#         'inventory.asset.type',
#         string='Asset Type',
#         # required=True
#     )
#     asset_category_id = fields.Many2one(
#         'inventory.asset.category',
#         string='Asset Category',
#         required=True
#     )
#     product_name_id = fields.Many2one(
#         'inventory.product',
#         string='Product Name',
#         required=True
#     )
#     brand_id = fields.Many2one(
#         'inventory.brand',
#         string='Brand',
#         required=True
#     )
#     model_id = fields.Many2one(
#         'inventory.model',
#         string='Model',
#         required=True
#     )
#
#     # One2many showing all inventory items for this model
#     inventory_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string='Inventory Items'
#     )
#
#     total_serial_count = fields.Integer(
#         string='Total Serial Numbers',
#         store=False
#     )
#
#     floor_id = fields.Many2one('estate.floor', string="Floor")
#     building_id = fields.Many2one('estate.building', string="Building")
#     property_id = fields.Many2one('estate.property', string="Property")
#     unit_id = fields.Many2one('estate.unit', string="Unit")
#     room_id = fields.Many2one('estate.room', string="Room")
#     allowed_asset_type_ids = fields.Many2many(
#         'inventory.asset.type',
#         compute='_compute_allowed_fields'
#     )
#
#     allowed_asset_category_ids = fields.Many2many(
#         'inventory.asset.category',
#         compute='_compute_allowed_fields'
#     )
#
#     allowed_product_ids = fields.Many2many(
#         'inventory.product',
#         compute='_compute_allowed_fields'
#     )
#
#     allowed_brand_ids = fields.Many2many(
#         'inventory.brand',
#         compute='_compute_allowed_fields'
#     )
#     inventory_product_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Inventory Products"
#     )
#
#     inventory_deployed_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         domain="[('in_charge','!=',False)]",
#         string="Deployed Products"
#     )
#     inventory_service_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Service & Repair"
#     )
#
#     inventory_retired_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Retired"
#     )
#
#     inventory_disposed_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Disposed"
#     )
#     total_count = fields.Integer(
#         string="Total",
#         compute="_compute_tab_counts"
#     )
#
#     inventory_product_count = fields.Integer(
#         string="Inventory Product",
#         compute="_compute_tab_counts"
#     )
#
#     deployed_count = fields.Integer(
#         string="Deployed Products",
#         compute="_compute_tab_counts"
#     )
#
#     service_count = fields.Integer(
#         string="Service & Repair Products",
#         compute="_compute_tab_counts"
#     )
#
#     retired_count = fields.Integer(
#         string="Retired Products" ,
#         compute="_compute_tab_counts"
#     )
#
#     disposed_count = fields.Integer(
#         string="Disposed Products",
#         compute="_compute_tab_counts"
#     )
#     warehouse_id = fields.Many2one(
#         'inventory.warehouse',
#         string="Warehouse",
#         # required=True,
#         tracking=True,
#         domain=lambda self: [
#             ('id', 'in',
#              self.env.user.warehouse_exec_ids.ids +
#              self.env.user.warehouse_manager_ids.ids
#              )
#         ]
#     )
#
#     def _validate_followers_against_warehouse(self, partners, vals=None):
#         for record in self:
#
#             warehouse = record.warehouse_id
#
#             if vals and vals.get('warehouse_id'):
#                 warehouse = self.env['inventory.warehouse'].browse(vals['warehouse_id'])
#
#             if not warehouse:
#                 continue
#
#             for partner in partners:
#                 user = partner.user_ids[:1]
#
#                 if not user:
#                     continue
#
#                 allowed_warehouses = (
#                         user.warehouse_exec_ids.ids +
#                         user.warehouse_manager_ids.ids
#                 )
#
#                 if warehouse.id not in allowed_warehouses:
#                     raise ValidationError(
#                         f"{user.name} is not assigned to warehouse '{warehouse.name}'."
#                     )
#
#     @api.depends('model_id')
#     def _compute_tab_counts(self):
#         for rec in self:
#             if not rec.model_id:
#                 rec.total_count = 0
#                 rec.inventory_product_count = 0
#                 rec.deployed_count = 0
#                 rec.service_count = 0
#                 rec.retired_count = 0
#                 rec.disposed_count = 0
#                 continue
#
#             all_inventory = self.env['custom.inventory'].search([
#                 ('model_id', '=', rec.model_id.id)
#             ])
#
#             rec.total_count = len(all_inventory)
#
#             rec.inventory_product_count = len(
#                 all_inventory.filtered(
#                     lambda r: r.lifecycle_state == 'in_stock'
#                 )
#             )
#
#             rec.deployed_count = len(
#                 all_inventory.filtered(
#                     lambda r: r.lifecycle_state == 'in_use'
#                 )
#             )
#
#             rec.service_count = len(
#                 all_inventory.filtered(
#                     lambda r: r.lifecycle_state == 'maintenance'
#                 )
#             )
#
#             rec.retired_count = len(
#                 all_inventory.filtered(
#                     lambda r: r.lifecycle_state == 'retired'
#                 )
#             )
#
#             rec.disposed_count = len(
#                 all_inventory.filtered(
#                     lambda r: r.lifecycle_state == 'disposed'
#                 )
#             )
#
#
#     @api.onchange('model_id', 'asset_type_id', 'asset_category_id')
#     def _onchange_model_id(self):
#         for rec in self:
#
#             # If no model selected → clear everything
#             if not rec.model_id:
#                 rec.inventory_ids = [(5, 0, 0)]
#                 rec.inventory_product_ids = [(5, 0, 0)]
#                 rec.inventory_deployed_ids = [(5, 0, 0)]
#                 rec.inventory_service_ids = [(5, 0, 0)]
#                 rec.inventory_retired_ids = [(5, 0, 0)]
#                 rec.inventory_disposed_ids = [(5, 0, 0)]
#                 rec.total_serial_count = 0
#                 return
#
#             # ------------------------------
#             # Build Dynamic AND Domain
#             # ------------------------------
#             domain = [('model_id', '=', rec.model_id.id)]
#
#             if rec.asset_type_id:
#                 domain.append(('asset_type_id', '=', rec.asset_type_id.id))
#
#             if rec.asset_category_id:
#                 domain.append(('asset_category_id', '=', rec.asset_category_id.id))
#
#             # Fetch filtered inventory
#             all_inventory = self.env['custom.inventory'].search(domain)
#
#             # TAB 1 → All
#             rec.inventory_ids = [(6, 0, all_inventory.ids)]
#             rec.total_serial_count = len(all_inventory)
#
#             # TAB 2 → Inventory Product
#             # TAB 2 → Inventory Product (In Stock Only)
#             rec.inventory_product_ids = [(6, 0,
#                                           all_inventory.filtered(
#                                               lambda r: r.lifecycle_state == 'in_stock'
#                                           ).ids
#                                           )]
#
#             # TAB 3 → Deployed
#             rec.inventory_deployed_ids = [(6, 0,
#                                            all_inventory.filtered(
#                                                lambda r: r.lifecycle_state == 'in_use'
#                                            ).ids
#                                            )]
#
#             # TAB 4 → Service & Repair
#             rec.inventory_service_ids = [(6, 0,
#                                           all_inventory.filtered(
#                                               lambda r: r.lifecycle_state == 'maintenance'
#                                           ).ids
#                                           )]
#
#             # TAB 5 → Retired
#             rec.inventory_retired_ids = [(6, 0,
#                                           all_inventory.filtered(
#                                               lambda r: r.lifecycle_state == 'retired'
#                                           ).ids
#                                           )]
#
#             # TAB 6 → Disposed
#             rec.inventory_disposed_ids = [(6, 0,
#                                            all_inventory.filtered(
#                                                lambda r: r.lifecycle_state == 'disposed'
#                                            ).ids
#                                            )]
#
#     @api.depends('model_id')
#     def _compute_allowed_fields(self):
#         for rec in self:
#
#             if not rec.model_id:
#                 rec.allowed_asset_type_ids = False
#                 rec.allowed_asset_category_ids = False
#                 rec.allowed_product_ids = False
#                 rec.allowed_brand_ids = False
#                 continue
#
#             inventory_records = self.env['custom.inventory'].search([
#                 ('model_id', '=', rec.model_id.id)
#             ])
#
#             rec.allowed_asset_type_ids = inventory_records.mapped('asset_type_id')
#             rec.allowed_asset_category_ids = inventory_records.mapped('asset_category_id')
#             rec.allowed_product_ids = inventory_records.mapped('product_name_id')
#             rec.allowed_brand_ids = inventory_records.mapped('brand_id')
#
#     @api.onchange('model_id')
#     def _onchange_model_fetch_product_brand(self):
#         for rec in self:
#             if rec.model_id:
#                 rec.product_name_id = rec.model_id.product_name_id
#                 rec.brand_id = rec.model_id.brand_id
#             else:
#                 rec.product_name_id = False
#                 rec.brand_id = False
#
#     def write(self, vals):
#
#         if 'message_partner_ids' in vals:
#             partner_ids = []
#
#             for command in vals.get('message_partner_ids'):
#                 if command[0] == 4:
#                     partner_ids.append(command[1])
#                 elif command[0] == 6:
#                     partner_ids.extend(command[2])
#
#             partners = self.env['res.partner'].browse(partner_ids)
#             self._validate_followers_against_warehouse(partners, vals)
#
#         return super().write(vals)
#
#     def message_subscribe(self, partner_ids=None, subtype_ids=None):
#         if partner_ids:
#             partners = self.env['res.partner'].browse(partner_ids)
#             self._validate_followers_against_warehouse(partners)
#
#         return super().message_subscribe(
#             partner_ids=partner_ids,
#             subtype_ids=subtype_ids
#         )































# from odoo import models, fields, api
# from odoo.exceptions import ValidationError
#
#
# class InventoryModelMaster(models.Model):
#     _name = 'inventory.model.master'
#     _description = 'Inventory Model Master'
#     _rec_name = 'model_id'
#     _inherit = ['mail.thread']
#
#     # ================= BASIC FIELDS =================
#
#     asset_type_id = fields.Many2one('inventory.asset.type', string='Asset Type')
#
#     asset_category_id = fields.Many2one(
#         'inventory.asset.category',
#         string='Asset Category',
#         required=True
#     )
#
#     product_name_id = fields.Many2one(
#         'inventory.product',
#         string='Product Name',
#         required=True
#     )
#
#     brand_id = fields.Many2one(
#         'inventory.brand',
#         string='Brand',
#         required=True
#     )
#
#     model_id = fields.Many2one(
#         'inventory.model',
#         string='Model',
#         required=True
#     )
#
#     warehouse_id = fields.Many2one(
#         'inventory.warehouse',
#         string="Warehouse",
#         tracking=True,
#         domain=lambda self: [
#             ('id', 'in',
#              self.env.user.warehouse_exec_ids.ids +
#              self.env.user.warehouse_manager_ids.ids)
#         ]
#     )
#
#     # ================= ONE2MANY (EDITABLE + FILTERED) =================
#
#     inventory_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string='Inventory Items',
#         domain="[('model_id','=',model_id), ('asset_type_id','=',asset_type_id), ('warehouse_id','=',warehouse_id)]"
#     )
#
#     inventory_product_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Inventory Products",
#         domain="[('model_id','=',model_id), ('asset_type_id','=',asset_type_id), ('warehouse_id','=',warehouse_id), ('lifecycle_state','=','in_stock')]"
#     )
#
#     inventory_deployed_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Deployed Products",
#         domain="[('model_id','=',model_id), ('asset_type_id','=',asset_type_id), ('warehouse_id','=',warehouse_id), ('lifecycle_state','=','in_use')]"
#     )
#
#     inventory_service_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Service & Repair",
#         domain="[('model_id','=',model_id), ('asset_type_id','=',asset_type_id), ('warehouse_id','=',warehouse_id), ('lifecycle_state','=','maintenance')]"
#     )
#
#     inventory_retired_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Retired",
#         domain="[('model_id','=',model_id), ('asset_type_id','=',asset_type_id), ('warehouse_id','=',warehouse_id), ('lifecycle_state','=','retired')]"
#     )
#
#     inventory_disposed_ids = fields.One2many(
#         'custom.inventory',
#         'model_master_ref_id',
#         string="Disposed",
#         domain="[('model_id','=',model_id), ('asset_type_id','=',asset_type_id), ('warehouse_id','=',warehouse_id), ('lifecycle_state','=','disposed')]"
#     )
#
#     # ================= COUNTS (ALWAYS MATCH TABS) =================
#
#     total_count = fields.Integer(compute="_compute_tab_counts")
#     inventory_product_count = fields.Integer(compute="_compute_tab_counts")
#     deployed_count = fields.Integer(compute="_compute_tab_counts")
#     service_count = fields.Integer(compute="_compute_tab_counts")
#     retired_count = fields.Integer(compute="_compute_tab_counts")
#     disposed_count = fields.Integer(compute="_compute_tab_counts")
#
#     @api.depends(
#         'inventory_ids.lifecycle_state',
#         'inventory_ids.model_id',
#         'inventory_ids.asset_type_id',
#         'inventory_ids.warehouse_id',
#         'model_id',
#         'asset_type_id',
#         'warehouse_id'
#     )
#     def _compute_tab_counts(self):
#         for rec in self:
#
#             # Apply SAME DOMAIN as tabs
#             domain = []
#
#             if rec.model_id:
#                 domain.append(('model_id', '=', rec.model_id.id))
#
#             if rec.asset_type_id:
#                 domain.append(('asset_type_id', '=', rec.asset_type_id.id))
#
#             if rec.warehouse_id:
#                 domain.append(('warehouse_id', '=', rec.warehouse_id.id))
#
#             all_records = self.env['custom.inventory'].search(domain)
#
#             rec.total_count = len(all_records)
#             rec.inventory_product_count = len(all_records.filtered(lambda r: r.lifecycle_state == 'in_stock'))
#             rec.deployed_count = len(all_records.filtered(lambda r: r.lifecycle_state == 'in_use'))
#             rec.service_count = len(all_records.filtered(lambda r: r.lifecycle_state == 'maintenance'))
#             rec.retired_count = len(all_records.filtered(lambda r: r.lifecycle_state == 'retired'))
#             rec.disposed_count = len(all_records.filtered(lambda r: r.lifecycle_state == 'disposed'))
#
#     # ================= AUTO SET PRODUCT / BRAND =================
#
#     @api.onchange('model_id')
#     def _onchange_model_fetch_product_brand(self):
#         for rec in self:
#             if rec.model_id:
#                 rec.product_name_id = rec.model_id.product_name_id
#                 rec.brand_id = rec.model_id.brand_id
#             else:
#                 rec.product_name_id = False
#                 rec.brand_id = False
#
#     # ================= FOLLOWER VALIDATION =================
#
#     def _validate_followers_against_warehouse(self, partners, vals=None):
#         for record in self:
#
#             warehouse = record.warehouse_id
#
#             if vals and vals.get('warehouse_id'):
#                 warehouse = self.env['inventory.warehouse'].browse(vals['warehouse_id'])
#
#             if not warehouse:
#                 continue
#
#             for partner in partners:
#                 user = partner.user_ids[:1]
#
#                 if not user:
#                     continue
#
#                 allowed_warehouses = (
#                     user.warehouse_exec_ids.ids +
#                     user.warehouse_manager_ids.ids
#                 )
#
#                 if warehouse.id not in allowed_warehouses:
#                     raise ValidationError(
#                         f"{user.name} is not assigned to warehouse '{warehouse.name}'."
#                     )
#
#     def write(self, vals):
#         if 'message_partner_ids' in vals:
#             partner_ids = []
#
#             for command in vals.get('message_partner_ids'):
#                 if command[0] == 4:
#                     partner_ids.append(command[1])
#                 elif command[0] == 6:
#                     partner_ids.extend(command[2])
#
#             partners = self.env['res.partner'].browse(partner_ids)
#             self._validate_followers_against_warehouse(partners, vals)
#
#         return super().write(vals)
#
#     def message_subscribe(self, partner_ids=None, subtype_ids=None):
#         if partner_ids:
#             partners = self.env['res.partner'].browse(partner_ids)
#             self._validate_followers_against_warehouse(partners)
#
#         return super().message_subscribe(
#             partner_ids=partner_ids,
#             subtype_ids=subtype_ids
#         )
#
#
