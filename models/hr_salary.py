# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

class HrSalary(models.Model):
    _name = 'hr.salary'
    _description = 'Employee Salary'

    name = fields.Char()
    start_date = fields.Date(string='Date début', required=True)
    end_date = fields.Date(string='Date fin', required=True)
    total_base_amount = fields.Float(string='Montant de base ', required=True)
    total_advance_amount = fields.Float(string='Montant Avance', default=0.0)
    total_other_deductions_amount = fields.Float(string='Montant autres déduction', default=0.0)
    total_net_payable = fields.Float(string='Net à payer', compute='_compute_total_net_payable', store=True)
    total_paid_amount = fields.Float(string='Montant payé', default=0.0)
    total_remaining_amount = fields.Float(string='Reste à payer', compute='_compute_total_remaining_amount', store=True)

    salary_line_ids = fields.One2many('hr.salary.line', 'salary_id', string='Salaires employés')

    @api.depends('total_base_amount', 'total_advance_amount', 'total_other_deductions_amount')
    def _compute_total_net_payable(self):
        for record in self:
            record.total_net_payable = record.total_base_amount - record.total_advance_amount - record.total_other_deductions_amount

    @api.depends('total_paid_amount', 'total_net_payable')
    def _compute_total_remaining_amount(self):
        for record in self:
            record.total_remaining_amount = record.total_net_payable - record.total_paid_amount

    @api.model
    def generate_salaries(self):
        employees = self.env['hr.employee'].search([('is_active', '=', True)])
        salary_lines = []
        salary_lines_ids = []
        for employee in employees:
            dict_values = {
                'employee_id': employee.id,
                'start_date': datetime.now().replace(day=1),
                'end_date': (datetime.now().replace(day=1, month=datetime.now().month + 1) - timedelta(days=1)).date(),
                'base_amount': employee.monthly_salary,
            }
            salary_lines.append(dict_values)
            salary_lines_ids.append((0, 0, dict_values))
        # MONTHS = {
        #     'jan' : 'Janvier',
        #     'feb' : 'Fevrier',
        #     'mar' : 'Mars',
        #     'apr' : 'Avril',
        #     'may' : 'Mai',
        #     'jun' : 'Juin',
        #     'jul' : 'Juillet',
        #     'aug' : 'Août',
        #     'sep' : 'Septembre',
        #     'oct' : 'Octobre',
        #     'nov' : 'Novembre',
        #     'dec' : 'Decembre',
        # }
        # month_name = str(datetime.now().strftime('%B'))[:3].lower()
        # name = "SALAIRE MOIS - {}".format(MONTHS[month_name].upper())
        import locale
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        name = "SALAIRE MOIS - {}".format(datetime.now().date().strftime('%B').upper())
        values = {
            'name': name,
            'start_date': datetime.now().replace(day=1),
            'end_date': (datetime.now().replace(day=1, month=datetime.now().month + 1) - timedelta(days=1)).date(),
            'total_base_amount': sum(salary['base_amount'] for salary in salary_lines),
            'salary_line_ids': salary_lines_ids
        }
        current_hr_salary = self.env['hr.salary'].search([('end_date', '=', values['end_date'])])
        if current_hr_salary:
            raise ValidationError(_('Salaires du mois déjà générés !'))
        self.env['hr.salary'].create(values)


class HrSalaryLine(models.Model):
    _name = 'hr.salary.line'
    _description = 'Employee Salary Line'

    salary_id = fields.Many2one('hr.salary', string='Salaire')
    salary_line_wiz_id = fields.Many2one('hr.salary.line.wizard', string="Ligne salaire")

    employee_id = fields.Many2one('hr.employee', string='Employé')
    start_date = fields.Date(string='Date début')
    end_date = fields.Date(string='Date fin')
    base_amount = fields.Float(string='Montant de base ')
    advance_type = fields.Char(string='Avance')
    advance_amount = fields.Float(string='Montant Avance', default=0.0)
    other_deductions = fields.Char(string='Autres deductionAutres deduction')
    other_deductions_amount = fields.Float(string='Montant autres déduction', default=0.0)
    net_payable = fields.Float(string='Net à payer', compute='_compute_net_payable', store=True)
    paid_amount = fields.Float(string='Montant payé', default=0.0)
    remaining_amount = fields.Float(string='Reste à payer', compute='_compute_remaining_amount', store=True)
    state = fields.Selection([('unpaid', 'Non payé'), ('paid', 'Payé')], default='unpaid', readonly=True)

    @api.depends('base_amount', 'advance_amount', 'other_deductions_amount')
    def _compute_net_payable(self):
        for record in self:
            record.net_payable = record.base_amount - record.advance_amount - record.other_deductions_amount

    @api.depends('paid_amount', 'net_payable')
    def _compute_remaining_amount(self):
        for record in self:
            record.remaining_amount = record.net_payable - record.paid_amount

    def action_pay(self):
        for record in self:
            import calendar
            import locale
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
            current_date = datetime.now().date()
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            last_date_of_month = current_date.replace(day=last_day)
            month_name = current_date.strftime('%B').capitalize()
            payment_method_id = self.env.ref('index_simple_salary.payment_method_bank_transfer').id
            current_context = self._context
            date = record.end_date
            salary_amount = 0.0
            if current_context['params']['model'] == 'hr.employee':
                emp_salary_line = self.env['hr.salary.line'].search([('employee_id', '=', current_context['params']['id'])])
                salary_amount = emp_salary_line.remaining_amount
                date = emp_salary_line.end_date
            if date:
                month_name = date.strftime('%B').capitalize()
            memo = "Paiement salaire ''{}''".format(month_name)
            context = {
                'default_amount' : salary_amount,
                'default_payment_date' : date,
                'default_communication' : memo,
                'default_payment_type': 'transfer', 
                'default_payment_method_id': payment_method_id,
                'search_default_transfers_filter': 1
            }
            return {
                'name': _('Enregistrer un paiement'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.payment',
                # 'view_id': self.env.ref('index_simple_salary.view_account_payment_employee_form').id,
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'new'
            }