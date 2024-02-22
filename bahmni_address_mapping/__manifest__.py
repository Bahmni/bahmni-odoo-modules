{
    'name': 'Bahmni Address Mapping',
    'version': '1.0',
    'summary': 'Module to add additional fields to the address model',
    'sequence': 1,
    'description': """
Bahmni Address Mapping
====================
""",
    'category': 'Services',
    'website': '',
    'images': [],
    'depends': [],
    'data': ['security/ir.model.access.csv',
             'data/data.xml',
             'views/res_partner_address_extension.xml',
             'views/address_mapping_table_view.xml'],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
