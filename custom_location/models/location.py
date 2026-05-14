from odoo import models, fields, api, _


class Location(models.Model):
    _name = 'custom.location'
    _description = 'Location Model'

    name = fields.Char(string="Coordinates")
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state = fields.Char(string="State")
    country = fields.Char(string="Country")
    pincode = fields.Char(string="Pincode")
    map_url = fields.Html(
        string="Google Map",
        compute="_compute_map_url",
        sanitize=False
    )


    @api.depends('name')
    def _compute_map_url(self):
        for rec in self:
            if rec.name:
                rec.map_url = f'''
                        <a href="https://www.google.com/maps?q={rec.name}"
                           target="_blank"
                           style="color:#008f8c;text-decoration:underline;">
                            View Map
                        </a>
                    '''
            else:
                rec.map_url = False