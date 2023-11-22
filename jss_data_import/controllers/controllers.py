# -*- coding: utf-8 -*-
# from odoo import http


# class JssDataImport(http.Controller):
#     @http.route('/jss_data_import/jss_data_import', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jss_data_import/jss_data_import/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('jss_data_import.listing', {
#             'root': '/jss_data_import/jss_data_import',
#             'objects': http.request.env['jss_data_import.jss_data_import'].search([]),
#         })

#     @http.route('/jss_data_import/jss_data_import/objects/<model("jss_data_import.jss_data_import"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jss_data_import.object', {
#             'object': obj
#         })
