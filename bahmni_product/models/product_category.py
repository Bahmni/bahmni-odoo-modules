
import uuid
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    uuid = fields.Char(string="UUID")

    @api.model
    def create(self, vals):
        if vals.get('uuid') is None or not vals.get('uuid'):
            vals.update({'uuid': uuid.uuid4()})
        return super(ProductCategory, self).create(vals)