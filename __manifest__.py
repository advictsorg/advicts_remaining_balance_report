# -*- coding: utf-8 -*-
{
    'name': 'Advicts Remaining Days Balance Report',
    'version': '1.1',
    'summary': "Generate reports for remaining time off days based on active contracts",
    'author': 'GhaithAhmed@Advicts',
    'category': 'Sale',
    'website': 'http://www.advicts.com',
    'description': """
    Generate reports for remaining time off days based on active contracts
    """,
    'depends': ['hr', 'hr_holidays', 'hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard.xml',
        'views/views.xml',
    ],

}
