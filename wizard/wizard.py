from odoo import models, api, fields, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from collections import defaultdict


class RemainingInfoReportWizard(models.TransientModel):
    _name = "remaining.days.wizard"
    _description = "Remaining days Report"

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    contract_id = fields.Many2one('hr.contract', string='Active Contract', compute='_compute_contract')
    start_date = fields.Date(string='Start Date', compute='_compute_date', readonly=False)
    end_date = fields.Date(string='End Date', compute='_compute_date', readonly=False)

    @api.depends('employee_id')
    def _compute_date(self):
        for record in self:
            if record.contract_id.date_start:
                record.start_date = record.contract_id.date_start
            else:
                record.start_date = False

            if record.contract_id.date_end:
                record.end_date = record.contract_id.date_end
            else:
                record.end_date = False

    @api.depends('employee_id')
    def _compute_contract(self):
        for record in self:
            record.contract_id = self.env['hr.contract'].search([
                ('employee_id', '=', record.employee_id.id),
                ('state', '=', 'open')
            ], limit=1)

    def _check_user_input(self):
        if not self.start_date:
            raise ValidationError(_("Please select a start date."))
        elif not self.end_date:
            raise ValidationError(_("Please select an end date."))
        elif self.end_date < self.start_date:
            raise ValidationError(_("End date cannot be before the start date."))
        return True

    def _get_report_data(self):
        self._check_user_input()
        self.env['timeoff.report'].search([]).unlink()

        leave_types = self.env['hr.leave.type'].search([('requires_allocation', '=', 'yes')])
        allocation_data = self._get_allocation_data(self.employee_id, leave_types, self.end_date)

        for leave_type, data in allocation_data[self.employee_id]:
            remaining_days = data['virtual_remaining_leaves']
            self.env['timeoff.report'].create({
                'employee_id': self.employee_id.id,
                'leave_type_id': leave_type.id,
                'remaining_days': remaining_days,
                'start_date': self.start_date,
                'end_date': self.end_date,
            })

    def _get_allocation_data(self, employee, leave_types, target_date):
        allocation_data = defaultdict(list)
        allocations_leaves_consumed = self._get_consumed_leaves(employee, leave_types, target_date)

        for leave_type in leave_types:
            lt_info = (
                leave_type,
                {
                    'remaining_leaves': 0,
                    'virtual_remaining_leaves': 0,
                    'max_leaves': 0,
                    'leaves_taken': 0,
                    'virtual_leaves_taken': 0,
                }
            )

            for allocation, data in allocations_leaves_consumed[employee][leave_type].items():
                if allocation.date_from <= target_date and (
                        not allocation.date_to or allocation.date_to >= target_date):
                    lt_info[1]['remaining_leaves'] += data['remaining_leaves']
                    lt_info[1]['virtual_remaining_leaves'] += data['virtual_remaining_leaves']
                    lt_info[1]['max_leaves'] += data['max_leaves']
                    lt_info[1]['leaves_taken'] += data['leaves_taken']
                    lt_info[1]['virtual_leaves_taken'] += data['virtual_leaves_taken']

            allocation_data[employee].append(lt_info)

        return allocation_data

    def _get_consumed_leaves(self, employee, leave_types, target_date):
        consumed_leaves = defaultdict(lambda: defaultdict(dict))
        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', '=', employee.id),
            ('state', '=', 'validate'),
            ('holiday_status_id', 'in', leave_types.ids),
        ])

        for allocation in allocations:
            leave_type = allocation.holiday_status_id
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type.id),
                ('state', '=', 'validate'),
                ('request_date_from', '<=', target_date),
                ('request_date_to', '>=', self.start_date),
            ])

            taken_days = sum(leaves.mapped('number_of_days'))
            virtual_taken_days = taken_days + sum(
                self.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('holiday_status_id', '=', leave_type.id),
                    ('state', 'not in', ['refuse', 'cancel']),
                    ('request_date_from', '>', target_date),
                ]).mapped('number_of_days')
            )

            consumed_leaves[employee][leave_type][allocation] = {
                'max_leaves': allocation.number_of_days,
                'leaves_taken': taken_days,
                'virtual_leaves_taken': virtual_taken_days,
                'remaining_leaves': max(0, allocation.number_of_days - taken_days),
                'virtual_remaining_leaves': max(0, allocation.number_of_days - virtual_taken_days),
            }

        return consumed_leaves

    def action_create_rem_report(self):
        self._get_report_data()
        return {
            'name': 'Remaining days Report',
            'type': 'ir.actions.act_window',
            'res_model': 'timeoff.report',
            'view_mode': 'tree',
        }
