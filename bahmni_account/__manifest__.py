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
    'depends': ['account','account_payment','sale'],
    'data': [
             'views/account_invoice_view.xml',
             'views/company_view.xml',
             ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
