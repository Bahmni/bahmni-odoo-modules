# -*- coding: utf-8 -*-
{
    'name': "Bahmni Custom Reports",

    'summary': """
        Generate Excel and PDF reports for Purchase and Sales Module. """,

    'description': """
        This module enables the generation of Excel and PDF reports 
        for stock products managed in Odoo.
        It provides functionalities to:
        - Generate Excel reports containing stock product details.
        - Create PDF reports summarizing stock product information.
        - Enhance stock management by exporting data for analysis or sharing.
        - Access insights into stock product inventory through reports. 
    """,

    'author': "Karthikeyan",
    'website': "https://www.bahmni.org/",
    'category': 'Customizations',
    'version': '0.1',
    'sequence': 1,

    # Dependencies
    'depends': ['base', 'stock', 'product', 'web'],

    # Always loaded XML data & security
    'data': [
        'security/ir.model.access.csv',
        'report/reports_menu_view.xml',
        'report/sale_discount_head_statement_view.xml',
        'report/purchase_order_register_view.xml',
        'report/product_expiration_register_view.xml',
        'report/expired_product_list_view.xml',
        'report/purchase_return_register_view.xml',
        'report/vendor_price_comparison_list_view.xml',
        'report/location_wise_drug_movement_view.xml',
        'report/active_product_statement_view.xml',
        'report/product_reorder_list_view.xml',
        'report/stock_report_view.xml',
        'report/stock_report_qweb.xml',
        'report/stock_report_template.xml',
        'report/purchase_order_inward_list_view.xml',
    ],

    # Odoo 19 Web Assets
    'assets': {
        'web.assets_backend': [
            'bahmni_reports/static/src/js/action_manager.js',
            'bahmni_reports/static/src/components/*/*.js',
            'bahmni_reports/static/src/components/*/*.xml',
            'bahmni_reports/static/src/components/*/*.scss',
        ],
    },

    'demo': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}