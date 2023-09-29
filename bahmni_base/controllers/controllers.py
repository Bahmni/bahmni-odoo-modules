# -*- coding: utf-8 -*-
# from odoo import http


# class CustomizedBase(http.Controller):
#     @http.route('/customized_base/customized_base', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customized_base/customized_base/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customized_base.listing', {
#             'root': '/customized_base/customized_base',
#             'objects': http.request.env['customized_base.customized_base'].search([]),
#         })

#     @http.route('/customized_base/customized_base/objects/<model("customized_base.customized_base"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customized_base.object', {
#             'object': obj
#         })
