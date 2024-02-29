# -*- coding: utf-8 -*-
# from odoo import http


# class BahmniReports(http.Controller):
#     @http.route('/bahmni_reports/bahmni_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bahmni_reports/bahmni_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bahmni_reports.listing', {
#             'root': '/bahmni_reports/bahmni_reports',
#             'objects': http.request.env['bahmni_reports.bahmni_reports'].search([]),
#         })

#     @http.route('/bahmni_reports/bahmni_reports/objects/<model("bahmni_reports.bahmni_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bahmni_reports.object', {
#             'object': obj
#         })
