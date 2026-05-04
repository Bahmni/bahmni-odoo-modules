{
    'name': 'Bahmni Base',
    'version': '1.0',
    'summary': 'Base module for Bahmni shared configurations',
    'sequence': 1,
    'description': """
Bahmni Base
====================
Provides shared configuration models used across Bahmni modules,
such as Company-Location mapping.
""",
    'category': 'Technical',
    'website': '',
    'images': [],
    'depends': ['base', 'bahmni_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/company_location_mapping_view.xml',
    ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
