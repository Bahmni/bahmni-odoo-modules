# -*- coding: utf-8 -*-
# from odoo import http


# class BahmniAtomFeed(http.Controller):
#     @http.route('/bahmni_atom_feed/bahmni_atom_feed', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bahmni_atom_feed/bahmni_atom_feed/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bahmni_atom_feed.listing', {
#             'root': '/bahmni_atom_feed/bahmni_atom_feed',
#             'objects': http.request.env['bahmni_atom_feed.bahmni_atom_feed'].search([]),
#         })

#     @http.route('/bahmni_atom_feed/bahmni_atom_feed/objects/<model("bahmni_atom_feed.bahmni_atom_feed"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bahmni_atom_feed.object', {
#             'object': obj
#         })
