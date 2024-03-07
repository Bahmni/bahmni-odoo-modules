# -*- coding: utf-8 -*-
# from odoo import http


# class Addons/bahmniInitializer/(http.Controller):
#     @http.route('/addons/bahmni_initializer//addons/bahmni_initializer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/addons/bahmni_initializer//addons/bahmni_initializer//objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('addons/bahmni_initializer/.listing', {
#             'root': '/addons/bahmni_initializer//addons/bahmni_initializer/',
#             'objects': http.request.env['addons/bahmni_initializer/.addons/bahmni_initializer/'].search([]),
#         })

#     @http.route('/addons/bahmni_initializer//addons/bahmni_initializer//objects/<model("addons/bahmni_initializer/.addons/bahmni_initializer/"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('addons/bahmni_initializer/.object', {
#             'object': obj
#         })
