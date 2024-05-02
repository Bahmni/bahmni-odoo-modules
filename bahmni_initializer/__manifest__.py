# -*- coding: utf-8 -*-
{
    'name': "Bahmni Initializer",
    'version': '0.1',
    'summary': """
        Module to read seed data from CSV/XML files and initialize the Bahmni Meta Data""",
    'description': """
Bahmni Initializer
==================
    """,
    'author': "Bahmni",
    'website': "https://www.yourcompany.com",
    'category': 'Services',
    'license': 'LGPL-3',
    'depends': ['base','bahmni_address_mapping','product','bahmni_product','bahmni_api_feed'],
    'data': [
        'security/ir.model.access.csv',
        'data/address.seed.csv',
        'data/uom_seed.xml',
        'data/sale_shop.xml',
        'data/order_type.xml'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}