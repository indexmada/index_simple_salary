# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import calendar
from datetime import datetime
import logging

class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    def action_validate_employee_payment(self):
        context = self._context
        if context['params']['model'] == 'hr.employee':
            emp_salary_line = self.env['hr.salary.line'].search([('employee_id', '=', context['params']['id']), ('end_date', '=', self.payment_date)], order='create_date desc', limit=1)
        elif context['params']['model'] == 'hr.salary' and context['active_model'] == 'hr.salary.line':
            emp_salary_line = self.env['hr.salary.line'].search([('id', '=', context['active_id']), ('end_date', '=', self.payment_date)], order='create_date desc', limit=1)
        if emp_salary_line:
            if emp_salary_line.state == 'paid':
                raise ValidationError(_('Salaire déjà payé !'))
            dict_value = {
                'state' : 'paid',
                'paid_amount' : self.amount
            }
            emp_salary_line.write(dict_value)

    @api.model
    def default_get(self, values):
        rec = super(InheritAccountPayment, self).default_get(values)
        current_context = self._context
        import locale
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        payment_method_id = self.env.ref('index_simple_salary.payment_method_bank_transfer').id
        if current_context['params']['model'] == 'hr.employee':
            emp_salary_line = self.env['hr.salary.line'].search([('employee_id', '=', current_context['params']['id'])], order='create_date desc', limit=1)
            current_date = datetime.now().date()
            month_name = current_date.strftime('%B').capitalize()
            memo = "Paiement salaire ''{}''".format(month_name)
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            last_date_of_month = current_date.replace(day=last_day)
            if 'default_communication' not in current_context:
                if emp_salary_line:
                    rec.update({
                        'amount' : emp_salary_line.remaining_amount,
                        'currency_id' : self.env.user.company_id.currency_id.id,
                        'payment_date' : last_date_of_month,
                        'communication' : memo,
                        'payment_type': 'transfer', 
                        'payment_method_id': payment_method_id,
                    })
        return rec