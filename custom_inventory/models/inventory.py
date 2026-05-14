from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import qrcode
import uuid
import base64
from io import BytesIO
from markupsafe import Markup

_logger = logging.getLogger(__name__)


# --------------------------
# Asset Type
# --------------------------
class InventoryAssetType(models.Model):
    _name = 'inventory.asset.type'
    _description = 'Asset Type'
    _inherit = ['mail.thread']

    name = fields.Char(string='Asset Type', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    example_tag = fields.Char(string='Example Tag', tracking=True)

    @api.constrains('name', 'code')
    def _check_unique_asset_type_code(self):
        for rec in self:
            domain = [('name', '=', rec.name), ('code', '=', rec.code)]
            if self.search_count(domain) > 1:
                raise ValidationError("Duplicate Asset Type with the same Code already exists.")


class MaintenanceCategory(models.Model):
    _name = 'maintenance.category'
    _description = 'Maintenance Category'
    _inherit = ['mail.thread']

    name = fields.Char(string='Category Name', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)


# --------------------------
# Asset Category
# --------------------------
class InventoryAssetCategory(models.Model):
    _name = 'inventory.asset.category'
    _description = 'Asset Category'
    _inherit = ['mail.thread']

    name = fields.Char(string='Asset Category', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)


# --------------------------
# Warehouse
# --------------------------
class InventoryWarehouse(models.Model):
    _name = 'inventory.warehouse'
    _description = 'Inventory Warehouse'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char(string='Warehouse', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    record_count = fields.Integer(
        string="Count",
        default=1,
        store=True
    )

# --------------------------
# Location / Sub Location / Cabin / Project / Product / Brand / Model
# --------------------------
class InventoryLocation(models.Model):
    _name = 'inventory.location'
    _description = 'Inventory Location'
    _inherit = ['mail.thread']

    name = fields.Char(string='Location', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    example_tag = fields.Char(string='Example Tag', tracking=True)


class InventorySubLocation(models.Model):
    _name = 'inventory.sub_location'
    _description = 'Inventory Sub Location'
    _inherit = ['mail.thread']

    name = fields.Char(string='Sub Location', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)


class InventoryCabin(models.Model):
    _name = 'inventory.cabin'
    _description = 'Inventory Cabin'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(string='Cabin', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)


class InventoryProject(models.Model):
    _name = 'inventory.project'
    _description = 'Inventory Project'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(string='Project', required=True, tracking=True)


class InventoryProduct(models.Model):
    _name = 'inventory.product'
    _description = 'Inventory Product'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(string='Product Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)


class InventoryBrand(models.Model):
    _name = 'inventory.brand'
    _description = 'Inventory Brand'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char(string='Brand', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)


class InventoryModel(models.Model):
    _name = 'inventory.model'
    _description = 'Inventory Model'
    _order = "id desc"
    _inherit = ['mail.thread']


    name = fields.Char(string='Model', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    product_name_id = fields.Many2one(
        'inventory.product',
        string='Product Name',
        required=True,
        tracking=True
    )
    warehouse_id = fields.Many2one(
        'inventory.warehouse',  # ✅ KEEP THIS
        string="Warehouse",
    )

    brand_id = fields.Many2one(
        'inventory.brand',
        string='Brand',
        required=True,
        tracking=True
    )


# --------------------------
# Maintenance History
# --------------------------
class InventoryMaintenance(models.Model):
    _name = 'inventory.maintenance'
    _description = 'Maintenance History'
    _order = 'date desc'
    _inherit = ['mail.thread']

    inventory_id = fields.Many2one('custom.inventory', string='Inventory Item', required=True,store=True)
    description = fields.Text(string='Description', required=True)
    maintenance_type = fields.Selection([
        ('repair', 'Repair'),
        ('replacement', 'Replacement'),
        ('upgrade', 'Upgrade'),
        ('inspection', 'Inspection'),
        ('service', 'Service')
    ], string='Type', required=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    technician = fields.Many2one('hr.employee', string='Performed By')
    cost = fields.Float(string='Cost')
    asset_tag = fields.Char(
        string="Asset Tag",
        store=True
    )
    maintenance_category_id = fields.Many2one(
        'maintenance.category',
        string='Maintenance Category',
        tracking=True
    )

    # ✅ NEW FIELD
    deadline_date = fields.Date(string='Deadline Date', tracking=True)

    # ✅ NEW FIELD
    sent_to_vendor = fields.Char(string='Sent to Vendor', tracking=True)

    def create(self, vals):
        rec = super().create(vals)

        if rec.inventory_id:
            rec.inventory_id._send_mail_to_followers(
                subject="Maintenance Created",
                body=Markup(f"""
                    <p>New maintenance created for:</p>
                    <b>{rec.inventory_id.asset_tag}</b>
                """)
            )

        return rec

    def write(self, vals):
        res = super().write(vals)

        for rec in self:
            if rec.inventory_id:
                rec.inventory_id._send_mail_to_followers(
                    subject="Maintenance Updated",
                    body=Markup(f"""
                        <p>Maintenance updated for:</p>
                        <b>{rec.inventory_id.asset_tag}</b>
                    """)
                )

        return res
# --------------------------
# Custom Inventory
# --------------------------
class CustomInventory(models.Model):
    _name = 'custom.inventory'
    _inherit = ['mail.thread']
    _description = 'Custom Inventory'
    _rec_name = "asset_tag"
    _order = "id desc"

    asset_type_id = fields.Many2one('inventory.asset.type', string='Asset Type', tracking=True)
    asset_category_id = fields.Many2one('inventory.asset.category', string='Asset Category', tracking=True,
                                        required=True)
    # warehouse_id = fields.Many2one('inventory.warehouse', string='Warehouse', tracking=True, required=True,
    #                                domain=lambda self: [
    #                                    ('id', 'in',
    #                                     self.env.user.warehouse_exec_ids.ids +
    #                                     self.env.user.warehouse_manager_ids.ids
    #                                     )
    #                                ])

    warehouse_id = fields.Many2one(
        'inventory.warehouse',
        string='Warehouse',
        domain="[('id', 'in', allowed_warehouse_ids)]"
    )
    allowed_warehouse_ids = fields.Many2many(
        'inventory.warehouse',
        compute='_compute_allowed_warehouses'
    )
    asset_owner = fields.Many2one('hr.employee', string='Assets Belong to', tracking=True)
    location_id = fields.Many2one('inventory.location', string='Location', tracking=True)
    sub_location_id = fields.Many2one('inventory.sub_location', string='Sub Location', tracking=True)
    cabin_id = fields.Many2one('inventory.cabin', string='Cabin', tracking=True)
    # project_id = fields.Many2one('inventory.project', string='Project', tracking=True)
    in_charge = fields.Many2one('hr.employee', string='In Charge', tracking=True)
    product_name_id = fields.Many2one('inventory.product', string='Product Name', tracking=True, required=True)
    brand_id = fields.Many2one('inventory.brand', string='Brand', tracking=True)
    model_id = fields.Many2one('inventory.model', string='Model', tracking=True, required=True)
    serial_no = fields.Char(string='Serial No', tracking=True, required=True)
    quantity = fields.Integer(string='Quantity', tracking=True)
    part_number = fields.Char(string='Part Number from Brand', tracking=True)
    purchase_date = fields.Date(string='Purchase Date', tracking=True, required=True)
    manufacture_date = fields.Date(string='Manufacture Date', tracking=True)
    warranty_start = fields.Date(string='Warranty Start', tracking=True)
    warranty_end = fields.Date(string='Warranty End', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    awb_or_bill_no = fields.Char(string='AWB / Consignment / Bill Number', tracking=True)
    asset_tag = fields.Char(string='Asset Tag', compute='_compute_asset_tag', store=True, tracking=True)
    is_trackable = fields.Boolean(string="Related Locations", default=True, tracking=True)
    part = fields.Char(string='Part Number', tracking=True, required=True)

    property_id = fields.Many2one('estate.property', string="Property")
    building_id = fields.Many2one('estate.building', string="Building")
    floor_id = fields.Many2one('estate.floor', string="Floor")
    unit_id = fields.Many2one('estate.unit', string="Unit")
    room_id = fields.Many2one('estate.room', string="Room")
    model_master_ref_id = fields.Many2one(
        'inventory.model.master',
        string='Model Master',
        index=True
    )

    lifecycle_state = fields.Selection([
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed'),
        ('in_stock', 'In Stock'),
    ], string="Lifecycle Status", default='in_use', tracking=True)

    maintenance_ids = fields.One2many('inventory.maintenance', 'inventory_id', string='Maintenance History')
    maintenance_count = fields.Integer(
        string="Maintenance Count",
        compute="_compute_maintenance_count"
    )
    qr_code = fields.Binary(
        string="QR Code",
        store=True,
        readonly=True
    )
    public_token = fields.Char(
        string="Public Token",
        copy=False,
        index=True
    )
    qr_text_data = fields.Text(
        string="QR Raw Data",
        compute="_compute_qr_text",
        store=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True
    )


    # ✅ NEW FIELDS
    rack = fields.Char(string="Rack", tracking=True)
    shelf = fields.Char(string="Shelf", tracking=True)
    cabinet = fields.Char(string="Cabinet", tracking=True)
    parent_asset_id = fields.Many2one(
        'custom.inventory',
        string="Parent Asset",
        tracking=True
    )

    sub_asset_ids = fields.Many2many(
        'custom.inventory',
        'custom_inventory_sub_asset_rel',
        'parent_id',
        'child_id',
        string="Sub Assets",
        tracking=True
    )
    sub_asset_count = fields.Integer(
        compute="_compute_sub_asset_count"
    )
    last_warranty_mail_days = fields.Integer(string="Last Warranty Reminder")
    last_expiry_mail_days = fields.Integer(string="Last Expiry Reminder")

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

    @api.depends('sub_asset_ids')
    def _compute_sub_asset_count(self):
        for rec in self:
            rec.sub_asset_count = len(rec.sub_asset_ids)

    def action_view_sub_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sub Assets',
            'res_model': 'custom.inventory',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sub_asset_ids.ids)],
            'context': {
                'default_parent_asset_id': self.id
            }
        }






    @api.constrains('parent_asset_id', 'sub_asset_ids')
    def _check_asset_hierarchy(self):
        for rec in self:

            # ❌ Self as parent
            if rec.parent_asset_id and rec.parent_asset_id.id == rec.id:
                raise ValidationError("Asset cannot be its own parent.")

            # ❌ Self in children
            if rec.id in rec.sub_asset_ids.ids:
                raise ValidationError("Asset cannot be its own sub asset.")

            # ❌ Parent inside children
            if rec.parent_asset_id and rec.parent_asset_id.id in rec.sub_asset_ids.ids:
                raise ValidationError(
                    "You cannot add parent asset as a sub asset."
                )
            if rec.parent_asset_id:
                duplicates = self.search([
                    ('id', '=', rec.id),
                    ('parent_asset_id', '!=', False),
                    ('parent_asset_id', '!=', rec.parent_asset_id.id)
                ])
                if duplicates:
                    raise ValidationError("Asset cannot have multiple parents.")





    def action_print_inventory_report(self):
        self.ensure_one()
        return self.env.ref(
            'custom_inventory.action_report_custom_inventory'
        ).report_action(self)

    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = len(rec.maintenance_ids)

    def action_view_maintenance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance History',
            'res_model': 'inventory.maintenance',
            'view_mode': 'list,form',
            'domain': [('inventory_id', '=', self.id)],
            'context': {
                'default_inventory_id': self.id
            }
        }

    # --------------------------
    # Auto populate room/floor/unit/building/property based on owner
    # --------------------------
    @api.onchange('asset_owner', 'in_charge')
    def _onchange_employee_location(self):
        for rec in self:

            # -------------------------------------------------
            # 🔥 Priority 1 → Asset Owner
            # -------------------------------------------------
            employee = rec.asset_owner or rec.in_charge

            if not employee:
                rec.property_id = False
                rec.building_id = False
                rec.floor_id = False
                rec.unit_id = False
                rec.room_id = False
                return

            # -------------------------------------------------
            # 🔍 Find Employee Table Assignment
            # -------------------------------------------------
            room_employee = self.env['estate.room.employee'].search([
                ('employee_id', '=', employee.id)
            ],order='id desc',limit=1)

            if room_employee and room_employee.table_id:

                table = room_employee.table_id

                # ✅ USE HUP FIELDS (AS YOU REQUESTED)
                rec.property_id = table.hup_property_id.id
                rec.building_id = table.hup_building_id.id
                rec.floor_id = table.hup_floor_id.id
                rec.unit_id = table.hup_unit_id.id
                rec.room_id = table.hup_room_id.id

            else:
                rec.property_id = False
                rec.building_id = False
                rec.floor_id = False
                rec.unit_id = False
                rec.room_id = False

    # --------------------------
    # Compute Asset Tag
    # --------------------------
    @api.depends(
        'warehouse_id.code', 'asset_type_id.code',
        'asset_category_id.code', 'product_name_id.code',
        'model_id.code', 'purchase_date', 'serial_no', 'part'
    )
    def _compute_asset_tag(self):
        for rec in self:
            if rec.warehouse_id and rec.asset_type_id and rec.asset_category_id and rec.product_name_id and rec.model_id:
                ym = rec.purchase_date.strftime('%Y%m') if rec.purchase_date else "000000"
                serial = rec.serial_no or "NOSERIAL"
                part = rec.part or "NOPART"
                rec.asset_tag = f"{rec.warehouse_id.code}-{rec.asset_type_id.code}-{rec.asset_category_id.code}-{rec.product_name_id.code}-{rec.model_id.code}-{ym}-{serial}-{part}"
            else:
                rec.asset_tag = ''

    # --------------------------
    # Overrides
    # --------------------------
    # def write(self, vals):
    #     for record in self:
    #         changes = {field: (record[field], vals[field]) for field in vals if field in record}
    #         _logger.info(f"[Inventory Log] Record {record.id} updated: {changes}")
    #     return super(CustomInventory, self).write(vals)
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #
    #     for vals in vals_list:
    #
    #         # If created from Model Master One2many
    #         if vals.get('model_master_ref_id'):
    #             master = self.env['inventory.model.master'].browse(
    #                 vals['model_master_ref_id']
    #             )
    #
    #             vals.update({
    #                 'asset_type_id': master.asset_type_id.id,
    #                 'asset_category_id': master.asset_category_id.id,
    #                 'product_name_id': master.product_name_id.id,
    #                 'brand_id': master.brand_id.id,
    #                 'model_id': master.model_id.id,
    #             })
    #
    #         # If created from Inventory screen (auto-link)
    #         if not vals.get('model_master_ref_id'):
    #             master = self.env['inventory.model.master'].search([
    #                 ('product_name_id', '=', vals.get('product_name_id')),
    #                 ('brand_id', '=', vals.get('brand_id')),
    #                 ('model_id', '=', vals.get('model_id')),
    #                 ('asset_type_id', '=', vals.get('asset_type_id')),
    #                 ('asset_category_id', '=', vals.get('asset_category_id')),
    #             ], limit=1)
    #
    #             if master:
    #                 vals['model_master_ref_id'] = master.id
    #
    #     return super(CustomInventory, self).create(vals_list)

    @api.depends('qr_text_data')
    def _compute_qr_code(self):
        for rec in self:
            if not rec.qr_text_data:
                rec.qr_code = False
                continue

            qr = qrcode.QRCode(
                version=None,
                box_size=20,
                border=4,
            )

            qr.add_data(rec.qr_text_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format="PNG")

            rec.qr_code = base64.b64encode(buffer.getvalue())

    # -------------------------------------------------
    # Auto Lifecycle based on Asset Owner
    # -------------------------------------------------
    @api.onchange('asset_owner')
    def _onchange_asset_owner(self):
        for rec in self:
            if rec.asset_owner:
                rec.lifecycle_state = 'in_use'

    # -------------------------------------------------
    # Clear Asset Owner for specific lifecycle states
    # -------------------------------------------------
    @api.onchange('lifecycle_state')
    def _onchange_lifecycle_state(self):
        for rec in self:
            if rec.lifecycle_state in ['maintenance', 'retired', 'disposed', 'in_stock']:
                rec.asset_owner = False

    @api.depends(
        'asset_tag', 'asset_type_id', 'asset_category_id',
        'warehouse_id', 'product_name_id', 'brand_id',
        'model_id', 'serial_no', 'quantity',
        'purchase_date', 'manufacture_date',
        'warranty_start', 'warranty_end',
        'expiry_date', 'awb_or_bill_no',
        'asset_owner', 'in_charge',
        'property_id', 'building_id',
        'floor_id', 'unit_id', 'room_id',
        'lifecycle_state', 'part', 'part_number',
        'is_trackable'
    )
    # def _compute_qr_text(self):
    #     for rec in self:
    #         rec.qr_text_data = f"""
    #
    #     ASSET IDENTIFICATION
    # ----------------------------------------
    # ASSET TAG        : {rec.asset_tag or '-'}
    # LIFECYCLE STATUS : {(rec.lifecycle_state or '-').upper()}
    # TRACKABLE        : {'YES' if rec.is_trackable else 'NO'}
    #
    # PRODUCT INFORMATION
    # ----------------------------------------
    # PRODUCT NAME     : {(rec.product_name_id.name or '-').upper() if rec.product_name_id else '-'}
    # BRAND            : {(rec.brand_id.name or '-').upper() if rec.brand_id else '-'}
    # MODEL            : {(rec.model_id.name or '-').upper() if rec.model_id else '-'}
    # SERIAL NUMBER    : {rec.serial_no or '-'}
    # QUANTITY         : {rec.quantity or 0}
    # PART             : {rec.part or '-'}
    # PART NUMBER      : {rec.part_number or '-'}
    #
    # ASSET CLASSIFICATION
    # ----------------------------------------
    # ASSET TYPE       : {(rec.asset_type_id.name or '-').upper() if rec.asset_type_id else '-'}
    # ASSET CATEGORY   : {(rec.asset_category_id.name or '-').upper() if rec.asset_category_id else '-'}
    # WAREHOUSE        : {(rec.warehouse_id.name or '-').upper() if rec.warehouse_id else '-'}
    #
    # RESPONSIBILITY
    # ----------------------------------------
    # ASSET OWNER      : {(rec.asset_owner.name or 'NOT ASSIGNED').upper() if rec.asset_owner else 'NOT ASSIGNED'}
    # IN CHARGE        : {(rec.in_charge.name or 'NOT ASSIGNED').upper() if rec.in_charge else 'NOT ASSIGNED'}
    #
    # PROPERTY LOCATION
    # ----------------------------------------
    # PROPERTY         : {(rec.property_id.name or '-').upper() if rec.property_id else '-'}
    # BUILDING         : {(rec.building_id.name or '-').upper() if rec.building_id else '-'}
    # FLOOR            : {(rec.floor_id.name or '-').upper() if rec.floor_id else '-'}
    # UNIT             : {(rec.unit_id.name or '-').upper() if rec.unit_id else '-'}
    # ROOM             : {(rec.room_id.name or '-').upper() if rec.room_id else '-'}
    #
    # IMPORTANT DATES
    # ----------------------------------------
    # PURCHASE DATE    : {rec.purchase_date or '-'}
    # MANUFACTURE DATE : {rec.manufacture_date or '-'}
    # WARRANTY START   : {rec.warranty_start or '-'}
    # WARRANTY END     : {rec.warranty_end or '-'}
    # EXPIRY DATE      : {rec.expiry_date or '-'}
    # AWB / BILL NO    : {rec.awb_or_bill_no or '-'}
    #
    #  .......GENERATED BY INVENTORY SYSTEM.......
    # """

    @api.depends('asset_tag', 'unit_id', 'room_id')
    def _compute_qr_text(self):
        for rec in self:
            rec.qr_text_data = f"""Asset Tag: {rec.asset_tag or '-'}
    Unit: {(rec.unit_id.name or '-') if rec.unit_id else '-'}
    Room: {(rec.room_id.name or '-') if rec.room_id else '-'}

    Inventory"""



























    # @api.depends(
    #     'asset_tag', 'product_name_id', 'brand_id',
    #     'model_id', 'serial_no', 'warehouse_id',
    #     'lifecycle_state', 'asset_category_id',
    #     'asset_type_id', 'quantity', 'part',
    #     'location_id'
    # )
    # def _compute_qr_text(self):
    #     for rec in self:
    #         rec.qr_text_data = (
    #             f"ASSET:{rec.asset_tag or '-'}\n"
    #             f"PRODUCT:{(rec.product_name_id.name or '-') if rec.product_name_id else '-'}\n"
    #             f"BRAND:{(rec.brand_id.name or '-') if rec.brand_id else '-'}\n"
    #             f"MODEL:{(rec.model_id.name or '-') if rec.model_id else '-'}\n"
    #             f"SERIAL:{rec.serial_no or '-'}\n"
    #             f"WAREHOUSE:{(rec.warehouse_id.name or '-') if rec.warehouse_id else '-'}\n"
    #             f"STATUS:{(rec.lifecycle_state or '-').upper()}\n"
    #             f"TYPE:{(rec.asset_type_id.name or '-') if rec.asset_type_id else '-'}\n"
    #             f"CATEGORY:{(rec.asset_category_id.name or '-') if rec.asset_category_id else '-'}\n"
    #             f"QUANTITY:{rec.quantity or 0}\n"
    #             f"PART:{rec.part or '-'}\n"
    #             f"LOCATION:{(rec.location_id.name or '-') if rec.location_id else '-'}"
    #         )

    # def _generate_qr_code(self):
    #     for rec in self:
    #         if not rec.qr_text_data:
    #             rec.qr_code = False
    #             continue
    #
    #         qr = qrcode.QRCode(
    #             version=None,
    #             box_size=14,
    #             border=4,
    #         )
    #
    #         qr.add_data(rec.qr_text_data)
    #         qr.make(fit=True)
    #
    #         img = qr.make_image(fill_color="black", back_color="white")
    #
    #         buffer = BytesIO()
    #         img.save(buffer, format="PNG")
    #
    #         rec.qr_code = base64.b64encode(buffer.getvalue())

    def _generate_qr_code(self):
        for rec in self:
            if not rec.qr_text_data:
                rec.qr_code = False
                continue

            qr = qrcode.QRCode(
                version=1,  # 🔥 FORCE SMALL QR
                error_correction=qrcode.constants.ERROR_CORRECT_L,  # 🔥 SMALL
                box_size=8,  # 🔥 VERY SMALL IMAGE
                border=1,  # 🔥 MIN BORDER
            )


            qr.add_data(rec.qr_text_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            buffer = BytesIO()
            img.save(buffer, format="PNG")

            rec.qr_code = base64.b64encode(buffer.getvalue())

    # -------------------------------------------------
    # WRITE
    # -------------------------------------------------
    def write(self, vals):

        if 'message_partner_ids' in vals:
            partner_ids = []

            for command in vals.get('message_partner_ids'):
                if command[0] == 4:
                    partner_ids.append(command[1])
                elif command[0] == 6:
                    partner_ids.extend(command[2])

            partners = self.env['res.partner'].browse(partner_ids)

            self._validate_followers_against_warehouse(partners)
        # Log Changes
        for record in self:
            changes = {
                field: (record[field], vals[field])
                for field in vals if field in record
            }
            _logger.info(f"[Inventory Log] Record {record.id} updated: {changes}")

        tracked_fields = [
            'asset_owner', 'in_charge',
            'property_id', 'building_id', 'unit_id',
            'floor_id', 'room_id',
            'rack', 'shelf', 'cabinet', 'project_id',
            'warranty_start', 'warranty_end', 'expiry_date'
        ]

        email_changes_map = {}

        for rec in self:
            changes = []

            for field in tracked_fields:
                if field in vals:
                    field_obj = rec._fields.get(field)

                    # MANY2ONE
                    if field_obj and field_obj.type == 'many2one':

                        old_name = rec[field].display_name if rec[field] else '-'

                        new_record = self.env[field_obj.comodel_name].browse(vals[field]) if vals[field] else False
                        new_name = new_record.display_name if new_record else '-'

                        if old_name != new_name:
                            changes.append((field, old_name, new_name))

                    # NORMAL FIELD
                    else:
                        old_name = rec[field] or '-'
                        new_name = vals[field] or '-'

                        if old_name != new_name:
                            changes.append((field, old_name, new_name))

            if changes:
                email_changes_map[rec.id] = changes
        res = super(CustomInventory, self).write(vals)
        if 'sub_asset_ids' in vals:
            for rec in self:
                for child in rec.sub_asset_ids:

                    # ❌ self check
                    if child.id == rec.id:
                        raise ValidationError("You cannot add the same asset as a sub asset.")

                    # ❌ cannot add parent as child
                    if rec.parent_asset_id and child.id == rec.parent_asset_id.id:
                        raise ValidationError("Parent asset cannot be added as sub asset.")

                    # ❌ child already has parent
                    if child.parent_asset_id and child.parent_asset_id.id != rec.id:
                        raise ValidationError(
                            f"{child.asset_tag} already has a parent assigned."
                        )

                    # ✅ SET PARENT
                    if child.parent_asset_id.id != rec.id:
                        child.sudo().write({
                            'parent_asset_id': rec.id
                        })

        # --------------------------
        # WHEN PARENT UPDATED
        # --------------------------
        if 'parent_asset_id' in vals:
            for rec in self:
                parent = rec.parent_asset_id

                if parent:

                    # ❌ self parent
                    if rec.id == parent.id:
                        raise ValidationError("Asset cannot be its own parent.")

                    # ❌ already has different parent
                    # if rec.parent_asset_id and rec.parent_asset_id.id != parent.id:
                    #     raise ValidationError(
                    #         f"This asset already has a parent: {rec.parent_asset_id.asset_tag}"
                    #     )
                    old_parent = rec._origin.parent_asset_id

                    if old_parent and old_parent.id != parent.id:
                        raise ValidationError(
                            f"This asset already has a parent: {old_parent.asset_tag}"
                        )

                    # ❌ cannot be both parent & child
                    if parent.id in rec.sub_asset_ids.ids:
                        raise ValidationError(
                            "Same asset cannot be both parent and child."
                        )

                    # ✅ ADD INTO PARENT
                    if rec.id not in parent.sub_asset_ids.ids:
                        parent.sudo().write({
                            'sub_asset_ids': [(4, rec.id)]
                        })

        # Regenerate QR only if important fields changed
        qr_trigger_fields = [
            'asset_tag', 'asset_type_id', 'asset_category_id',
            'warehouse_id', 'product_name_id', 'brand_id',
            'model_id', 'serial_no', 'quantity',
            'purchase_date', 'manufacture_date',
            'warranty_start', 'warranty_end',
            'expiry_date', 'awb_or_bill_no',
            'asset_owner', 'in_charge',
            'property_id', 'building_id',
            'floor_id', 'unit_id', 'room_id',
            'lifecycle_state'
        ]

        if any(field in vals for field in qr_trigger_fields):
            self._compute_qr_text()
            self._generate_qr_code()

        for rec in self:
            changes = email_changes_map.get(rec.id)

            # if changes:
            #     rows = ""
            #     for field, old, new in changes:
            #         rows += f"""
            #             <tr>
            #                 <td>{field}</td>
            #                 <td>{old}</td>
            #                 <td>{new}</td>
            #             </tr>
            #         """
            if changes:
                rows = ""
                for field, old, new in changes:
                    field_label = rec._fields[field].string

                    rows += f"""
                                <tr>
                                    <td>{field_label}</td>
                                    <td>{old}</td>
                                    <td>{new}</td>
                                </tr>
                            """

                rec._send_mail_to_followers(
                    subject="Inventory Updated",
                    body=Markup(f"""
                                <p><b>Asset:</b> {rec.asset_tag}</p>
                                <p>The following changes were made:</p>

                                <table border="1" cellpadding="5">
                                    <tr>
                                        <th>Field</th>
                                        <th>Old Value</th>
                                        <th>New Value</th>
                                    </tr>
                                    {rows}
                                </table>
                            """)
                )

        return res

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------
    # @api.model_create_multi
    # def create(self, vals_list):
    #
    #     for vals in vals_list:
    #
    #         # ------------------------------
    #         # If created from Model Master
    #         # ------------------------------
    #         if vals.get('model_master_ref_id'):
    #             master = self.env['inventory.model.master'].browse(
    #                 vals['model_master_ref_id']
    #             )
    #
    #             vals.update({
    #                 'asset_type_id': master.asset_type_id.id,
    #                 'asset_category_id': master.asset_category_id.id,
    #                 'product_name_id': master.product_name_id.id,
    #                 'brand_id': master.brand_id.id,
    #                 'model_id': master.model_id.id,
    #             })
    #
    #         # ------------------------------
    #         # If created from Inventory screen
    #         # ------------------------------
    #         else:
    #             master = self.env['inventory.model.master'].search([
    #                 ('product_name_id', '=', vals.get('product_name_id')),
    #                 ('brand_id', '=', vals.get('brand_id')),
    #                 ('model_id', '=', vals.get('model_id')),
    #                 ('asset_type_id', '=', vals.get('asset_type_id')),
    #                 ('asset_category_id', '=', vals.get('asset_category_id')),
    #             ], limit=1)
    #
    #             if master:
    #                 vals['model_master_ref_id'] = master.id
    #
    #     # Create records first
    #     records = super(CustomInventory, self).create(vals_list)
    #     for record, vals in zip(records, vals_list):
    #         if vals.get('message_partner_ids'):
    #             partner_ids = []
    #
    #             for command in vals.get('message_partner_ids'):
    #                 if command[0] == 4:
    #                     partner_ids.append(command[1])
    #                 elif command[0] == 6:
    #                     partner_ids.extend(command[2])
    #
    #             partners = self.env['res.partner'].browse(partner_ids)
    #
    #             record._validate_followers_against_warehouse(partners)
    #     # Generate QR only after record is saved
    #     records._compute_qr_text()
    #     records._generate_qr_code()
    #
    #     return records

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            master = False

            # ------------------------------
            # CASE 1: Created from Model Master
            # ------------------------------
            if vals.get('model_master_ref_id'):
                master = self.env['inventory.model.master'].browse(
                    vals['model_master_ref_id']
                )

            # ------------------------------
            # CASE 2: Created from Inventory Screen
            # ------------------------------
            else:
                # 🔥 PRIMARY MATCH (based on model_id — YOUR REQUIREMENT)
                if vals.get('model_id'):
                    master = self.env['inventory.model.master'].search([
                        ('model_id', '=', vals.get('model_id'))
                    ], limit=1)

                # 🔁 FALLBACK MATCH (your old logic — kept safe)
                if not master:
                    master = self.env['inventory.model.master'].search([
                        ('product_name_id', '=', vals.get('product_name_id')),
                        ('brand_id', '=', vals.get('brand_id')),
                        ('model_id', '=', vals.get('model_id')),
                        ('asset_type_id', '=', vals.get('asset_type_id')),
                        ('asset_category_id', '=', vals.get('asset_category_id')),
                    ], limit=1)

                if master:
                    vals['model_master_ref_id'] = master.id

            # ------------------------------
            # SYNC FIELDS FROM MASTER (COMMON)
            # ------------------------------
            if master:
                vals.update({
                    'asset_type_id': master.asset_type_id.id,
                    'asset_category_id': master.asset_category_id.id,
                    'product_name_id': master.product_name_id.id,
                    'brand_id': master.brand_id.id,
                    'model_id': master.model_id.id,
                    'warehouse_id': master.warehouse_id.id if master.warehouse_id else False,
                })

        # ------------------------------
        # CREATE RECORDS
        # ------------------------------
        records = super(CustomInventory, self).create(vals_list)

        # ------------------------------
        # FOLLOWER VALIDATION (UNCHANGED)
        # ------------------------------
        for record, vals in zip(records, vals_list):
            if vals.get('message_partner_ids'):
                partner_ids = []

                for command in vals.get('message_partner_ids'):
                    if command[0] == 4:
                        partner_ids.append(command[1])
                    elif command[0] == 6:
                        partner_ids.extend(command[2])

                partners = self.env['res.partner'].browse(partner_ids)
                record._validate_followers_against_warehouse(partners)

        # ------------------------------
        # QR GENERATION (UNCHANGED)
        # ------------------------------
        records._compute_qr_text()
        records._generate_qr_code()

        return records

    def _validate_followers_against_warehouse(self, partners, vals=None):
        for record in self:

            # 🔥 USE NEW VALUE IF PRESENT
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
                        f"{user.name} is not assigned to warehouse '{warehouse.name}'. "
                        f"You cannot add this user as follower."
                    )

    def cron_inventory_reminder(self):
        today = fields.Date.today()

        records = self.search([
            '|',
            ('warranty_end', '!=', False),
            ('expiry_date', '!=', False)
        ])

        notify_days = [60, 45, 30, 15, 7]

        for rec in records:

            # ================= WARRANTY =================
            if rec.warranty_end:
                delta = (rec.warranty_end - today).days

                send = False

                if delta in notify_days:
                    send = True
                elif delta <= 7:
                    send = True

                # if send and rec.last_warranty_mail_days != delta:
                if send and (delta <= 7 or rec.last_warranty_mail_days != delta):
                    status = "Expired" if delta < 0 else f"{delta} days left"

                    for partner in rec.message_partner_ids:

                        if not partner.email:
                            continue

                        body = f"""
                        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">

                            <p>Hello {partner.name},</p>

                            <p>
                                This is a reminder regarding the <b>warranty status</b> of the following asset:
                            </p>

                            <table style="border-collapse: collapse; margin-top: 10px;">
                                <tr>
                                    <td><b>Asset Tag</b></td>
                                    <td>{rec.asset_tag}</td>
                                </tr>
                                <tr>
                                    <td><b>Warranty End</b></td>
                                    <td>{rec.warranty_end}</td>
                                </tr>
                                <tr>
                                    <td><b>Status</b></td>
                                    <td><b>{status}</b></td>
                                </tr>
                            </table>

                            <p>Regards,<br/>{self.env.company.name}</p>

                        </div>
                        """

                        self.env['mail.mail'].create({
                            'subject': "Warranty Reminder",
                            'body_html': body,
                            'email_to': partner.email,
                            'auto_delete': False,
                        }).send()

                        # chatter once
                        rec.message_post(
                            subject="Warranty Reminder",
                            body=Markup(body),
                            message_type='comment'
                        )

                    # rec._send_mail_to_followers(
                    #     subject="Warranty Reminder",
                    #     body=f"""
                    #     <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
                    #
                    #         <p>Hello {self.env.user.name},</p>
                    #
                    #         <p>
                    #             This is a reminder regarding the <b>warranty status</b> of the following asset:
                    #         </p>
                    #
                    #         <table style="border-collapse: collapse; margin-top: 10px;">
                    #             <tr>
                    #                 <td style="padding: 6px 12px;"><b>Asset Tag</b></td>
                    #                 <td style="padding: 6px 12px;">{rec.asset_tag}</td>
                    #             </tr>
                    #             <tr>
                    #                 <td style="padding: 6px 12px;"><b>Warranty End Date</b></td>
                    #                 <td style="padding: 6px 12px;">{rec.warranty_end or '-'}</td>
                    #             </tr>
                    #             <tr>
                    #                 <td style="padding: 6px 12px;"><b>Status</b></td>
                    #                 <td style="padding: 6px 12px; color: {'red' if 'Expired' in status else '#d48806'};">
                    #                     <b>{status}</b>
                    #                 </td>
                    #             </tr>
                    #         </table>
                    #
                    #         <p style="margin-top: 15px;">
                    #             Please take the necessary action to review or renew the warranty if required.
                    #         </p>
                    #
                    #         <p>
                    #             Regards,<br/>
                    #             <b>{self.env.company.name}</b>
                    #         </p>
                    #
                    #     </div>
                    #     """
                    # )

                    # 🔥 IMPORTANT: use sudo write (NO interference)
                    rec.sudo().write({
                        'last_warranty_mail_days': delta
                    })

            # ================= EXPIRY =================
            if rec.expiry_date:
                delta = (rec.expiry_date - today).days

                send = False

                if delta in notify_days:
                    send = True
                elif delta <= 7:
                    send = True

                if send and (delta <= 7 or rec.last_expiry_mail_days != delta):
                    # if send and rec.last_expiry_mail_days != delta:
                    status = "Expired" if delta < 0 else f"{delta} days left"

                    for partner in rec.message_partner_ids:

                        if not partner.email:
                            continue

                        body = f"""
                        <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">

                            <p>Hello {partner.name},</p>

                            <p>
                                This is to notify you about the <b>expiry status</b> of the following asset:
                            </p>

                            <table>
                                <tr>
                                    <td><b>Asset Tag</b></td>
                                    <td>{rec.asset_tag}</td>
                                </tr>
                                <tr>
                                    <td><b>Expiry Date</b></td>
                                    <td>{rec.expiry_date}</td>
                                </tr>
                                <tr>
                                    <td><b>Status</b></td>
                                    <td><b>{status}</b></td>
                                </tr>
                            </table>

                            <p>Regards,<br/>{self.env.company.name}</p>

                        </div>
                        """

                        self.env['mail.mail'].create({
                            'subject': "Expiry Reminder",
                            'body_html': body,
                            'email_to': partner.email,
                            'auto_delete': False,
                        }).send()

                        # chatter once
                        rec.message_post(
                            subject="Expiry Reminder",
                            body=Markup(body),
                            message_type='comment'
                        )

                    # rec._send_mail_to_followers(
                    #     subject="Expiry Reminder",
                    #     body=f"""
                    #     <div style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
                    #
                    #         <p>Hello {self.env.user.name},</p>
                    #
                    #         <p>
                    #             This is to notify you about the <b>expiry status</b> of the following asset:
                    #         </p>
                    #
                    #         <table style="border-collapse: collapse; margin-top: 10px;">
                    #             <tr>
                    #                 <td style="padding: 6px 12px;"><b>Asset Tag</b></td>
                    #                 <td style="padding: 6px 12px;">{rec.asset_tag}</td>
                    #             </tr>
                    #             <tr>
                    #                 <td style="padding: 6px 12px;"><b>Expiry Date</b></td>
                    #                 <td style="padding: 6px 12px;">{rec.expiry_date or '-'}</td>
                    #             </tr>
                    #             <tr>
                    #                 <td style="padding: 6px 12px;"><b>Status</b></td>
                    #                 <td style="padding: 6px 12px; color: {'red' if 'Expired' in status else '#d48806'};">
                    #                     <b>{status}</b>
                    #                 </td>
                    #             </tr>
                    #         </table>
                    #
                    #         <p style="margin-top: 15px;">
                    #             Kindly take appropriate action to renew or review this asset to avoid disruptions.
                    #         </p>
                    #
                    #         <p>
                    #             Regards,<br/>
                    #             <b>{self.env.company.name}</b>
                    #         </p>
                    #
                    #     </div>
                    #     """
                    # )

                    rec.sudo().write({
                        'last_expiry_mail_days': delta
                    })

    def _send_mail_to_followers(self, subject, body):
        Mail = self.env['mail.mail']

        for rec in self:

            # ---------------- GET FOLLOWERS EMAILS
            emails = []

            for partner in rec.message_partner_ids:
                if partner.email:
                    emails.append(partner.email)

            if not emails:
                continue

            # ---------------- CREATE EMAIL (VISIBLE IN TECHNICAL)
            mail = Mail.create({
                'subject': subject,
                'body_html': body,
                'email_to': ','.join(emails),
                'auto_delete': False,
            })

            mail.send()

            # ---------------- ALSO POST IN CHATTER
            rec.message_post(
                subject=subject,
                body=Markup(body),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

    def message_subscribe(self, partner_ids=None, subtype_ids=None):
        if partner_ids:
            partners = self.env['res.partner'].browse(partner_ids)

            # 🔥 VALIDATION HERE
            self._validate_followers_against_warehouse(partners)

        return super(CustomInventory, self).message_subscribe(
            partner_ids=partner_ids,
            subtype_ids=subtype_ids
        )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity is not None and rec.quantity <= 0:
                raise ValidationError("Quantity must be greater than 0.")


class ResUsers(models.Model):
    _inherit = 'res.users'

    # warehouse_ids = fields.Many2many(
    #     'inventory.warehouse',  # ✅ KEEP THIS
    #     string="Warehouse",
    # )
    warehouse_exec_ids = fields.Many2many(
        'inventory.warehouse',
        'res_users_exec_warehouse_rel',
        'user_id',
        'warehouse_id',
        string="Executive Warehouses"
    )

    warehouse_manager_ids = fields.Many2many(
        'inventory.warehouse',
        'res_users_manager_warehouse_rel',
        'user_id',
        'warehouse_id',
        string="Manager Warehouses"
    )

    @api.constrains('warehouse_manager_ids', 'warehouse_exec_ids')
    def _check_warehouse_roles(self):
        for user in self:
            # The '&' operator finds common records between two recordsets
            common_warehouses = user.warehouse_manager_ids & user.warehouse_exec_ids

            if common_warehouses:
                # Extract names for a clear error message
                warehouse_names = ", ".join(common_warehouses.mapped('name'))
                raise ValidationError(
                    f"A person cannot be both a Manager and an Executive "
                    f"for the same warehouse: {warehouse_names}."
                )


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    # @api.model
    # def _message_get_suggested_recipients(self, *args, **kwargs):
    #     result = super()._message_get_suggested_recipients(*args, **kwargs)
    #
    #     user = self.env.user
    #
    #     # 🔥 COMBINE BOTH ROLES
    #     all_warehouses = (
    #             user.warehouse_exec_ids.ids +
    #             user.warehouse_manager_ids.ids
    #     )
    #
    #     # No warehouses → no filtering
    #     if not all_warehouses:
    #         return result
    #
    #     allowed_partner_ids = self.env['res.partner'].search([
    #         '|',
    #         ('user_ids.warehouse_exec_ids', 'in', all_warehouses),
    #         ('user_ids.warehouse_manager_ids', 'in', all_warehouses)
    #     ]).ids
    #
    #     # 🔥 ODOO 18/19 FORMAT (LIST)
    #     if isinstance(result, list):
    #         return [
    #             (partner_id, name, reason)
    #             for partner_id, name, reason in result
    #             if partner_id in allowed_partner_ids
    #         ]
    #
    #     # 🔥 OLD FORMAT (DICT)
    #     if isinstance(result, dict):
    #         for res_id, recipients in result.items():
    #             result[res_id] = [
    #                 (pid, name, reason)
    #                 for pid, name, reason in recipients
    #                 if pid in allowed_partner_ids
    #             ]
    #         return result
    @api.model
    def _message_get_suggested_recipients(self, *args, **kwargs):
        result = super()._message_get_suggested_recipients(*args, **kwargs)

        user = self.env.user

        all_warehouses = (
                user.warehouse_exec_ids.ids +
                user.warehouse_manager_ids.ids
        )

        if not all_warehouses:
            return result

        allowed_partner_ids = self.env['res.partner'].search([
            '|',
            ('user_ids.warehouse_exec_ids', 'in', all_warehouses),
            ('user_ids.warehouse_manager_ids', 'in', all_warehouses)
        ]).ids

        # 🔥 LIST FORMAT
        if isinstance(result, list):
            filtered = []
            for rec in result:

                # CASE 1: tuple/list
                if isinstance(rec, (list, tuple)):
                    partner_id = rec[0]

                # CASE 2: dict (ODOO 19)
                elif isinstance(rec, dict):
                    partner_id = rec.get('partner_id')

                else:
                    continue

                if partner_id in allowed_partner_ids:
                    filtered.append(rec)

            return filtered

        # 🔥 DICT FORMAT
        if isinstance(result, dict):
            for res_id, recipients in result.items():
                new_list = []

                for rec in recipients:

                    if isinstance(rec, (list, tuple)):
                        partner_id = rec[0]

                    elif isinstance(rec, dict):
                        partner_id = rec.get('partner_id')

                    else:
                        continue

                    if partner_id in allowed_partner_ids:
                        new_list.append(rec)

                result[res_id] = new_list

            return result

        return result


