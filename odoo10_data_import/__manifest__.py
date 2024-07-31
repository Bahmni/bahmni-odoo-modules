{
    'name': "Odoo 10 Data Import",

    'summary': """
        This model is specifically designed to migrate the Odoo 10(Bahmni) database data to the Odoo 16 database""",

    'description': """
        Overall, this module is intended to migrate data from one database to the current module's running database, 
        with the option to configure the database settings directly from the configuration

    """,

    'author': "Karthikeyan",
    'website': "https://bahmni.org",
    'category': 'Customizations',
    'version': '0.1',
    'depends': ['base'],
    'external_dependencies': {
        'python': ['python-decouple']
    },
    'data': [
        'views/db_details_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'post_init_hook': '_create_demo_config_param',
}
