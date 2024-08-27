# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
from datetime import datetime
import calendar

class InheritHrEmployee(models.Model):
    _inherit = 'hr.employee'

    monthly_salary = fields.Float(string='Salaire du mois', track_visibility='always')
    hiring_date = fields.Date(string='Date d\'embauche', track_visibility='always')
    end_contract_date = fields.Date(string='Date fin du contrat', track_visibility='always')
    is_active = fields.Boolean(track_visibility='always')

    unpaid_salary = fields.Float(compute='_compute_unpaid_salary')

    def _compute_unpaid_salary(self):
        emp_hr_salary_line = self.env['hr.salary.line'].search([('employee_id', '=', self.id)])
        sum_unpaid_salary = sum(emp.remaining_amount for emp in emp_hr_salary_line if emp.state == 'unpaid')
        for employee in self:
            employee.unpaid_salary = sum_unpaid_salary

    def show_hr_salary_line(self):
        # retrieve one employee salary line
        emp_hr_salary_line = self.env['hr.salary.line'].search([('employee_id', '=', self.id)])
        salary_line_ids = []
        if emp_hr_salary_line:
            for line in emp_hr_salary_line:
                dict_value = {
                    'employee_id' : line.employee_id.id,
                    'start_date' : line.start_date,
                    'end_date' : line.end_date,
                    'base_amount' : line.base_amount,
                    'advance_type' : line.advance_type,
                    'advance_amount' : line.advance_amount,
                    'other_deductions' : line.other_deductions,
                    'other_deductions_amount' : line.other_deductions_amount,
                    'net_payable' : line.net_payable,
                    'paid_amount' : line.paid_amount,
                    'remaining_amount' : line.remaining_amount,
                    'state' : line.state,
                }
                salary_line_ids.append((0, 0, dict_value))
        context_value = {
            'default_hr_salary_line_ids' : salary_line_ids
        }
        return {
            'name': _('Détail de salaire'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.salary.line.wizard',
            'view_id': self.env.ref('index_simple_salary.view_hr_salary_line_wizard_form').id,
            'type': 'ir.actions.act_window',
            'context': context_value,
            'target': 'new'
        }
    
    @api.multi
    def toggle_active(self):
        """ Change contract to inactive when employee gets archived. """
        res = super(InheritHrEmployee, self).toggle_active()
        emp_id = self.env['hr.employee'].search([('id', '=', self.id)])
        # if not emp_id.active:
        #     emp_id.is_active = False
        active_id = self.filtered(lambda rec: rec.active)
        is_active = 'false'
        if not active_id:
            self._cr.execute(
                """
                UPDATE hr_employee 
                SET is_active = %s
                WHERE id = %s;
                """,
                (is_active, self.id)
            )
        return res
