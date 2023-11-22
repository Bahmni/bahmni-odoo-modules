# -*- coding: utf-8 -*-
{
    'name': 'Bahmni Purchase',
    'version': '1.0',
    'summary': 'Custom purchase module to meet bahmni requirement',
    'sequence': 1,
    'description': """
Bahmni Purchase
====================
""",
    'category': 'Product',
    'website': '',
    'images': [],
    'depends': ['purchase', 'bahmni_product', 'bahmni_stock'],
    'data': [
	     'views/purchase_views.xml',
             'views/product_view.xml',
             'views/price_markup_table_view.xml'],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
