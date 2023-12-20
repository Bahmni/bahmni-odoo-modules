import functools
import logging
import werkzeug.wrappers
import json
import base64
import datetime
import functools
from odoo import http
from odoo.addons.restful_api.common import (
    extract_arguments,
    invalid_response,
    valid_response,
)
from odoo.http import request

_logger = logging.getLogger(__name__)

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

def validate_token(func):
    """."""
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        """."""
        access_token = request.httprequest.headers.get("Authorization") 
        if not access_token:
            return {
                     "status":401,
                     'error': 'Missing access token'
                   }
        
        access_token_data = (request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1))

        if (access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id)
            != access_token):

            return {
                     "status":401,
                     'error': 'Invalid access token.'
                   }

        request.session.uid = access_token_data.user_id.id
        request.id = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]


class RestFullService(http.Controller):
    @http.route('/api/bahmni-saleorder', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_saleorder_creation(self, **kw):
        """  API Sale order creation from bahmin to Odoo """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return  responce #{'status':200,'message': request.env['api.event.worker'].process_event(json_data)}
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }

    @http.route('/api/bahmni-customer', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_customer_feed(self, **kw):
        """  API customer feed from bahmin to Odoo """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return  responce 
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }

    @http.route('/api/bahmni-drug', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_drug_feed(self, **kw):
        """  API Drug feed from bahmin to Odoo """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return responce 
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }

    @http.route('/api/bahmni-radiology-test', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_rediology_test(self, **kw):
        """  Rediology test API """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return  responce 
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }

    @http.route('/api/bahmni-lab-test', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_lab_test(self, **kw):
        """  Lab test API """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return  responce 
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }

    @http.route('/api/bahmni-lab-panel', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_lab_panel(self, **kw):
        """  Lab Panel API """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return  responce 
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }

    @http.route('/api/bahmni-service-sale', type="json", auth="none", methods=["POST","OPTIONS"], csrf=True, cors='*')
    @validate_token
    def bahmni_service_sale(self, **kw):
        """  Service Sale API """
        json_data = json.loads(request.httprequest.data)
        try:
            if json_data:
               responce = request.env['api.event.worker'].process_event(json_data)
               return  responce 
        except Exception as e:
            return {
                     "status":417,
                     'error': 'Expectation Failed: ' + str(e)
                   }
