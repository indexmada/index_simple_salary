# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

class HrSalaryLineWizard(models.Model):
    _name = 'hr.salary.line.wizard'

    hr_salary_line_ids = fields.One2many('hr.salary.line', 'salary_line_wiz_id', string='Ligne de salaire')