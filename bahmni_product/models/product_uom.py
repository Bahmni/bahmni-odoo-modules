import uuid

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductUom(models.Model):
    _inherit = 'uom.uom'

    uuid = fields.Char(string="UUID")

    @api.model
    def create(self, vals):
        try:
            if vals.get('uuid') is None or not vals.get('uuid'):
                vals.update({'uuid': uuid.uuid4()})
            record = super(ProductUom, self).create(vals)
            _logger.info("Created New Unit of Measure {} With Id {}.".format(*(vals.get("name"), record.id)))
            return record
        except Exception as error:
            _logger.error("Failed To Create New Unit of Measure {}".format(vals.get("name")))

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
