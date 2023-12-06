import uuid

from odoo import models, fields, api


class ProductUom(models.Model):
    _inherit = 'uom.uom'

    uuid = fields.Char(string="UUID")

    @api.model
    def create(self, vals):
        if vals.get('uuid') is None or not vals.get('uuid'):
            vals.update({'uuid': uuid.uuid4()})
        return super(ProductUom, self).create(vals)

# need to override this method to reverse sync updated data
    def write(self, vals):
        return super(ProductUom, self).write(vals)


class ProductUomCategory(models.Model):
    _inherit = 'uom.category'

    uuid = fields.Char(string="UUID")

    @api.model
    def create(self, vals):
        if vals.get('uuid') is None or not vals.get('uuid'):
            vals.update({'uuid': uuid.uuid4()})
        return super(ProductUomCategory, self).create(vals)

# need to override this method to reverse sync updated data
    def write(self, vals):
        self.ensure_one()
        return super(ProductUomCategory, self).write(vals)
