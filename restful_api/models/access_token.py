import hashlib
import logging
import os
from datetime import datetime, timedelta
import random
import base64

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

expires_in = "restful_api.access_token_expires_in"

class APIAccessToken(models.Model):
    _name = "api.access_token"

    token = fields.Char("Access Token", required=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    expires = fields.Datetime("Expires", required=True)

    def find_one_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = (
            self.env["api.access_token"]
            .search([("user_id", "=", user_id)], order="id DESC", limit=1)
        )
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            expires = datetime.now() + timedelta(
                seconds=int(self.env.ref(expires_in).value)
            )

        if not access_token:
            return None
        return access_token.token

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.expires)

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

class Users(models.Model):
    _inherit = "res.users"
    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")

###########################################################################################
