import uuid
from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    uuid = fields.Char(string="UUID")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('uuid'):
                vals['uuid'] = str(uuid.uuid4())
        return super(ProductCategory, self).create(vals_list)