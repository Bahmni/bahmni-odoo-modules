#-*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class RestfulApi(http.Controller):
    @http.route('/restful_api/restful_api', auth='public')
    def index(self, **kw):
        vendor = request.env['res.partner'].search_count([])
        return "Totally %s vendor avilable now!"

    @http.route('/api/products', csrf=False, auth='public', methods=['GET', 'POST'])
    def product_list(self, **kw):
        data = [{
                'id': drug.id,
                'name': drug.name,
                'price': drug.list_price,
                } for drug in request.env['product.template'].search([])]
        return str(data)

#     @http.route('/restful_api/restful_api/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('restful_api.listing', {
#             'root': '/restful_api/restful_api',
#             'objects': http.request.env['restful_api.restful_api'].search([]),
#         })

#     @http.route('/restful_api/restful_api/objects/<model("restful_api.restful_api"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('restful_api.object', {
#             'object': obj
#         })
