from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class OrderType(models.Model):
    _name = 'order.type'
    _description = 'Order Type'

    name = fields.Char(string='Name', required=True, help='Name of the order type')
    description = fields.Text(string='Description', help='Description of the order type')

    _sql_constraints = [('unique_name', 'unique(name)', 'Order type with this name already exists!')]

    @api.model
    def create(self,vals):
        try:
            record = super(OrderType,self).create(vals)
            _logger.info("Created New Order Type {} With Id {}.".format(*(vals.get("name"),record.id)))
            return record
        except Exception as error:
            _logger.error("Failed To Create New Order Type {}".format(vals.get("name")))