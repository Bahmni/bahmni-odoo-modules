# -*- coding: utf-8 -*-
{
    'name': 'Bahmni Account',
    'version': '1.0',
    'summary': 'Custom account module to meet bahmni requirement',
    'sequence': 1,
    'description': """
Bahmni Account
====================
""",
    'category': 'Account',
    'website': '',
    'images': [],
    'depends': ['account'],
    'data': [
             'views/bahmni_account.xml',
             'views/account_invoice_view.xml',
             'views/account_config_settings.xml',
             'views/company_view.xml',
             'views/account_payment.xml',
             ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
