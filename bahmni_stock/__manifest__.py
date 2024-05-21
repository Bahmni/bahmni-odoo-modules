
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
    'depends': ['stock', 'bahmni_product'],
    'data': ['security/ir.model.access.csv',
             'views/stock_production_lot_view.xml',
             'views/stock_picking_view.xml',
             'views/account_invoice_line.xml',
             'views/stock_pick_lot_view.xml',
             'wizard/stock_picking_validate_wizard.xml',
             ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
