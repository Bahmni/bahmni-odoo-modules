# -*- coding: utf-8 -*-
{
    'name': "Restful_API",

    'summary': """ RESTful API """,

    'description': """
        Odoo's RESTful API allows external applications and services to access and 
        manipulate data stored within the Odoo database. This includes data 
        related to customers, products, invoices, sales orders, and more.
    """,

    'author': "Hari",
    'website': "https://www.bahmni.org",
    'category': 'API',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'data/ir_config_param.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',    
}
