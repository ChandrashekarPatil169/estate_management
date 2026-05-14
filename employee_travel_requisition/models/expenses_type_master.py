from odoo import models, fields

class TravelExpenseType(models.Model):
    _name = 'travel.expense.type'
    _description = 'Travel Expense Type'

    name = fields.Char(string="Expense Type", required=True)
    active = fields.Boolean(default=True)

class TravelMode(models.Model):
    _name = 'travel.mode'
    _description = 'Travel Mode Master'

    name = fields.Char(string="Mode Name", required=True)
    active = fields.Boolean(default=True)

class TravelStatus(models.Model):
    _name = 'travel.status'
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)



class TravelPurpose(models.Model):
    _name = 'travel.purpose'
    name = fields.Char(required=True)
    active = fields.Boolean(default=True)