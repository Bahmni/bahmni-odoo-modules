import uuid

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductUom(models.Model):
    _inherit = 'uom.uom'

    uuid = fields.Char(string="UUID")

    @api.model_create_multi
    def create(self, vals_list):
        try:
            for vals in vals_list:
                if vals.get('uuid') is None or not vals.get('uuid'):
                    vals.update({'uuid': uuid.uuid4()})
            records = super(ProductUom, self).create(vals_list)
            for vals, record in zip(vals_list, records):
                _logger.info("Created New Unit of Measure {} With Id {}.".format(*(vals.get("name"), record.id)))
            return records
        except Exception as error:
            _logger.error("Failed To Create New Unit of Measure(s) {}".format([vals.get("name") for vals in vals_list]))

    # need to override this method to reverse sync updated data
    def write(self, vals):
        return super(ProductUom, self).write(vals)
