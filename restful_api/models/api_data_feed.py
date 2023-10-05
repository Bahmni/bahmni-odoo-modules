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
            return invalid_response(401, "Missing access token",)
        
        access_token_data = (request.env["api.access_token"].sudo().search([("token", "=", access_token)], order="id DESC", limit=1))

        if (access_token_data.find_one_or_create_token(user_id=access_token_data.user_id.id)
            != access_token):

            return invalid_response(
                401, "Missing access token", 
            )

        request.session.uid = access_token_data.user_id.id
        request.id = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

_routes = ["/api/<model>", "/api/<model>/<id>", "/api/<model>/<id>/<action>"]


class RestFullService(http.Controller):
    @http.route('/api/bahmni_data', type="json", auth="none", methods=["POST","OPTIONS"], csrf=False, cors='*')
    #@validate_token
    def bahmni_data_feed(self, **kw):
        """  Atom data feed from bahmin to Odoo16 """
        try:
            if kw:
                atom_rec = request.env['api.event.worker'].process_event(kw.get('data'))
            return {'status':200,'message':'Customer Created Successfully'}
        except Exception as e:
            return {'error': 'An unexpected error occurred: ' + str(e)}
