{
    'name': 'Bahmni Seed Setup',
    'version': '1.0',
    'summary': 'Custom csv data seed setup bahmni requirement',
    'sequence': 1,
    'description': """
        Bahmni Seed Setup
        ====================
        """,
    'author': "Karthikeyan",
    'category': 'Customizations',
    'website': '',
    'images': [],
    'depends': ['base','bahmni_sale'],
    'data': [             
             'data/state.district.csv',            
             'data/district.tehsil.csv',
             'data/village.village.csv',
             ],
    'demo': [],
    'qweb': [],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
