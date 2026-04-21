from odoo import fields, models, api


class ProductInventoryService(models.Model):
    _name = 'product.inventory.service'
    _description = 'Product Inventory Service'
    _auto = False

    @api.model
    def get_available_batches(self, product_uuid):
        product = self.env['product.product'].sudo().search(
            [('uuid', '=', product_uuid)], limit=1
        )
        if not product:
            return None

        quants = self.env['stock.quant'].sudo().search([
            ('product_id', '=', product.id),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
            ('lot_id', '!=', False),
        ])

        result = []
        for quant in quants:
            if quant.lot_id.expiration_date and quant.lot_id.expiration_date < fields.Datetime.now():
                continue
            result.append({
                'product_name': quant.product_id.name,
                'product_uuid': quant.product_id.uuid,
                'location_name': quant.location_id.complete_name,
                'batch_number': quant.lot_id.name,
                'expiry_date': quant.lot_id.expiration_date.isoformat() if quant.lot_id.expiration_date else None,
                'available_quantity': quant.quantity,
            })

        return result
