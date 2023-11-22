# -*- coding: utf-8 -*-
{
    'name': 'Bahmni API Feed',
    'version': '1.0',
    'summary': 'Module to sync Bahmni with Odoo',
    'sequence': 1,
    'description': """
Bahmni API Feed
====================
""",
    'category': 'Technical',
    'website': '',
    'images': [],
    'depends': ['base','product'],
    'data': [
    'security/ir.model.access.csv',
         'data/mrs_person_attributes_data.xml',
	     'views/event_records_view.xml',
             'views/res_company.xml',
             'views/order_type_view.xml',
             'views/syncable_units_mapping_view.xml',
             'views/order_type_shop_map_view.xml',
             'views/res_users_view.xml',
             
             ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
