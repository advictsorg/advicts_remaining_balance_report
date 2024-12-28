from odoo import models, fields, api
from datetime import date


class TimeOffReport(models.Model):
    _name = 'timeoff.report'
    _description = 'Remaining Days Report'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave Type', required=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    remaining_days = fields.Float(string='Remaining Days')

