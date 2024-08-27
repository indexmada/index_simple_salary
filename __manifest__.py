# -*- coding: utf-8 -*-

{
    'name': 'Index Simple Salary',
    'version': '1.0',
    'author': 'Henintsoa Moriaa',
    'category': 'hr',
    'website': '',
    'depends': ['account', 'hr', 'base'],
    'license': "AGPL-3",
    'data': [
        'security/ir.model.access.csv',

        'data/data.xml',
        'data/ir_cron.xml',

        'wizard/hr_salary_line_wizard.xml',

        'views/hr_salary_view.xml',
        'views/inherit_account_payment_view.xml',
        'views/inherit_hr_employee_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
