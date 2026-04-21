import logging

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ProductInventoryService(models.AbstractModel):
    _name = 'product.inventory.service'
    _description = 'Product Inventory Service'

    @api.model
    def _get_non_expired_available_quants(self, product_id, location_id=None, check_reserved=True):
        """Return stock.quant recordset of non-expired lots with available stock > 0.

        :param product_id: ID of the product.product record
        :param location_id: Optional ID of a specific stock.location.
                            If None, searches all internal locations.
        :param check_reserved: If True (default), also filters out quants where
                               quantity - reserved_quantity <= 0.
                               Set to False when callers apply their own availability logic
                               (e.g. encounter-level allocation deductions).
        :returns: Filtered stock.quant recordset
        """
        domain = [
            ('product_id', '=', product_id),
            ('quantity', '>', 0),
            ('lot_id', '!=', False),
        ]
        if location_id:
            domain.append(('location_id', '=', location_id))
        else:
            domain.append(('location_id.usage', '=', 'internal'))

        quants = self.env['stock.quant'].search(domain)
        now = fields.Datetime.now()

        if check_reserved:
            return quants.filtered(
                lambda q: (not q.lot_id.expiration_date or q.lot_id.expiration_date > now)
                          and (q.quantity - q.reserved_quantity) > 0
            )
        return quants.filtered(
            lambda q: not q.lot_id.expiration_date or q.lot_id.expiration_date > now
        )

    @api.model
    def get_available_batches(self, product_uuid):
        """Return non-expired, available-stock lot/batch data for the given product UUID."""
        product = self.env['product.product'].search(
            [('uuid', '=', product_uuid)], limit=1
        )
        if not product:
            return None

        quants = self._get_non_expired_available_quants(product.id)

        quants.mapped('lot_id')
        quants.mapped('product_id')
        quants.mapped('location_id')
        quants.mapped('company_id')

        result = []
        for quant in quants:
            available_qty = quant.quantity - quant.reserved_quantity
            result.append({
                'product_name': quant.product_id.name,
                'product_uuid': quant.product_id.uuid,
                'location_name': quant.location_id.complete_name,
                'company_name': quant.company_id.name,
                'batch_number': quant.lot_id.name,
                'expiry_date': quant.lot_id.expiration_date.isoformat() if quant.lot_id.expiration_date else None,
                'available_quantity': available_qty,
            })

        return result
