# Part of odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from urllib import response
import werkzeug.wrappers
import hashlib
import os
from base64 import b64encode
from os import urandom

from odoo import http
from odoo.addons.restful_api.common import invalid_response, valid_response
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import datetime

_logger = logging.getLogger(__name__)

def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()

expires_in = "restful_api.access_token_expires_in"

#--------------------------------- Access_Key Login url ----------------------------------------#

class AccessToken(http.Controller):
    """."""

    def __init__(self):

        self._token = request.env["api.access_token"]
        self._expires_in = request.env.ref(expires_in).value

    @http.route("/api/odoo-login", methods=["POST","OPTIONS"], type="json", auth="none", csrf=True, cors='*')
    def token(self, **post):
        try:
            json_data = json.loads(request.httprequest.data)
            input_user_name = json_data.get("username"),
            input_password = json_data.get("password")
            if input_user_name[0] != None and input_user_name[0] != None:
                res_usersss = request.env['res.users'].search([
                    ('active','=',True),
                    ('login','=',input_user_name[0])])

                if res_usersss:
                    assert input_password
                    request.env.cr.execute(
                        "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                        [res_usersss.id]
                    )
                    [hashed] = request.env.cr.fetchone()
                    valid, replacement = res_usersss._crypt_context()\
                        .verify_and_update(input_password, hashed)
                    if replacement is not None:
                        res_usersss._set_encrypted_password(res_usersss.id, replacement)
                    if not valid:
                        return {
                                "error": {
                                            "status":401,
                                            "code": "invalid_credentials",
                                            "message": "Incorrect password. Please provide the correct password."
                                         }
                               }
                    request.env.company_id = 1  ###set company_id based logic users 
                    exp = datetime.datetime.utcnow() + datetime.timedelta(days=1)

                    rbytes = os.urandom(64)
                    random_pass = str(hashlib.sha256(rbytes).hexdigest())

                    token_values = request.env['api.access_token'].create({
                                'user_id': res_usersss.id,
                                'expires': exp.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                'token': str(random_pass)})

                    token_key_visible = {
                                            "status":200,
                                            "message":"Success",
                                            "data":
                                                {
                                                        "user_id": res_usersss.id,    
                                                        "username": input_user_name[0],
                                                        "access_token": str(random_pass),
                                                }
                                        }
                
                    
                    return token_key_visible
            
                else:
                    return {'status':401,'message':'Wrong Username & Password. Check the account is in ERP once and try again.'}
            else :
                return {'status':401,'message':'Username & Password is must'}

        except Exception as e:
            return {'error': 'An unexpected error occurred: ' + str(e)}
######################################################################################

