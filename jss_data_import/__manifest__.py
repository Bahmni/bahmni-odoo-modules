# -*- coding: utf-8 -*-
{
    'name': "JSS Data Import",

    'summary': """
        This model is specifically designed to migrate the OpenERP 7 database data to the Odoo 16 database, 
        with a particular focus on meeting the requirements of JSS.""",

    'description': """
        Overall, this module is intended to migrate data from one database to the current module's running database, 
        with the option to configure the database settings directly from the configuration

        Use the blow key for database connection:\n
            JSS_DB_HOST = "127.0.0.1"
            JSS_DB_PORT = "5432"
            JSS_DB_NAME = "database_name"
            JSS_DB_USER = "user_name"
            JSS_DB_PASSWORD = "password"
      
      Notes: Add .env file before installing the module.
    """,

    'author': "Hari",
    'website': "https://bahmni.org",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],
    'external_dependencies': {
        'python': ['python-decouple']
    },
    # always loaded
    'data': [
        'data/ir_cron_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
    'icon': 'static/src/icon.png',
    'post_init_hook': '_create_demo_config_param',
}
