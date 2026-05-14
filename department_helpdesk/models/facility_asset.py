from odoo import models, fields

class FacilityAsset(models.Model):
    _name = 'facility.asset'
    _description = 'Facility Asset'

    name = fields.Char(required=True, tracking=True)

    asset_type = fields.Selection([
        ('ahu', 'AHU'),
        ('elevator', 'Elevator'),
        ('pump', 'Pump'),
        ('generator', 'Generator'),
    ], string="Asset Type", required=True, tracking=True)

    serial_number = fields.Char(string="Serial Number", tracking=True)

    warranty_start_date = fields.Date(string="Warranty Start", tracking=True)
    warranty_end_date = fields.Date(string="Warranty End", tracking=True)


class FacilityContract(models.Model):
    _name = 'facility.contract'
    _description = 'Facility Contract'

    name = fields.Char(required=True, tracking=True)
    vendor_id = fields.Many2one('res.partner', tracking=True)
    start_date = fields.Date()
    end_date = fields.Date()


class FacilityPermit(models.Model):
    _name = 'facility.permit'
    _description = 'Facility Permit'

    name = fields.Char(required=True, tracking=True)
    permit_number = fields.Char()
    valid_from = fields.Date()
    valid_to = fields.Date()
