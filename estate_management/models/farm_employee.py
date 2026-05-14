from odoo import models, fields

class EstateFarmEmployee(models.Model):
    _name = 'estate.farm.employee'
    _inherit = ['mail.thread']  # <-- Add this
    _description = 'Farm Employee Assignment'
    _order = "id desc"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, tracking=True)
    farm_id = fields.Many2one('estate.farm', string="Assigned Farm", tracking=True)
    crop_id = fields.Many2one('estate.crop.name', string="Assigned Crop", tracking=True)
    task_id = fields.Many2one('estate.farm.task', string="Assigned Task", tracking=True)
    building_id = fields.Many2one('estate.building', tracking=True)
    unit_id = fields.Many2one('estate.unit', tracking=True)
    room_id = fields.Many2one('estate.room', tracking=True)

    wage = fields.Float(string="Wage / Salary", tracking=True)
    work_schedule = fields.Text(tracking=True)
    attendance_notes = fields.Text(tracking=True)
