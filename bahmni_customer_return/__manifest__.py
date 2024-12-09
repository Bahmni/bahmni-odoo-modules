# -*- coding: utf-8 -*-
{
    'name': "Bahmni Customer Sales Return",
    'summary': """Customized Bahmni Customer Sales Return module""",
    'description': """ To support a simplified return flow, a user form needs to be designed wherein the customer can be selected and the product items can be entered. """,
    'author': "Karthikeyan S",
    'website': "https://www.bahmni.org",
    'category': 'Sales',
    "license": "LGPL-3",
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['base','mail','product',"bahmni_sale"],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/bahmni_customer_return_views.xml',
        'views/res_config_inherit.xml',
    ],
  
}
