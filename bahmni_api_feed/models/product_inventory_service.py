import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ProductInventoryService(models.Model):
    _name = 'product.inventory.service'
    _description = 'Product Inventory Service'
    _auto = False

    @api.model
    def get_available_batches(self, product_uuid):
        product = self.env['product.product'].search(
            [('uuid', '=', product_uuid)], limit=1
        )
        if not product:
            return None

        quants = self.env['stock.quant'].search([
            ('product_id', '=', product.id),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
            ('lot_id', '!=', False),
        ])

        now = fields.Datetime.now()
        result = []
        for quant in quants:
            if quant.lot_id.expiration_date and quant.lot_id.expiration_date < now:
                continue

            available_qty = quant.quantity - quant.reserved_quantity
            if available_qty <= 0:
                continue

            result.append({
                'product_name': quant.product_id.name,
                'product_uuid': quant.product_id.uuid,
                'location_name': quant.location_id.complete_name,
                'company_name': quant.company_id.name,
                'batch_number': quant.lot_id.name,
                'expiry_date': (
                    quant.lot_id.expiration_date.strftime('%Y-%m-%dT%H:%M:%SZ')
                    if quant.lot_id.expiration_date
                    else None
                ),
                'available_quantity': available_qty,
            })

        return result
