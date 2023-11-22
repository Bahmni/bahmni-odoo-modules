# -*- coding: utf-8 -*-
{
    'name': 'Bahmni Stock',
    'version': '1.0',
    'summary': 'Custom stock module to meet bahmni requirement',
    'sequence': 1,
    'description': """
Bahmni Purchase
====================
""",
    'category': 'Stock',
    'website': '',
    'images': [],
    'depends': ['stock', 'bahmni_product', 'bahmni_account'],
    'data': ['views/stock_production_lot_view.xml',
             'views/stock_picking_view.xml',
             'views/account_invoice_line.xml',
             'views/account_payment_view.xml',
             ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
