

{
    'name': 'BR Custom List View',
    'version': '16.0.1.0.1',
    'summary': 'Helps to Show Row Number, Fixed Header, Duplicate Record and Highlight Selected Record in List View',
    'description': 'Helps to Show Row Number, Fixed Header, Duplicate Record and Highlight Selected Record in List View',
    'category': 'Tools',
    'author': 'Banibro IT Solutions Pvt Ltd.',
    'company': 'Banibro IT Solutions Pvt Ltd.',
    'website': 'https://banibro.com',
    'license': 'AGPL-3',
    'email': "support@banibro.com",
    'images': ['static/description/banner.png',
               'static/description/icon.png',],
    'depends': ['base'],
    'assets': {
        'web.assets_backend': [
            'br_custom_list_view/static/src/js/duplicate_record.js',
            'br_custom_list_view/static/src/js/record_highlight.js',
            'br_custom_list_view/static/src/css/sticky_header.css',
            'br_custom_list_view/static/src/css/highlight.css',
            'br_custom_list_view/static/src/xml/record_highlight.xml'
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
