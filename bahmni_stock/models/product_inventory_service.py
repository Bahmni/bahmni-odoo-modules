import logging
from datetime import datetime

from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class ProductInventoryService(models.AbstractModel):
    _name = 'product.inventory.service'
    _description = 'Product Inventory Service'

    @api.model
    def _build_quant_domain(self, product_id, location_id=None, company_id=None):
        """Build the base stock.quant search domain for a product.

        :param product_id: ID of the product.product record
        :param location_id: Optional ID of a specific stock.location.
                            If None, searches all internal locations.
        :param company_id: Optional ID of a res.company record.
                           If provided, filters quants by company (indexed column).
        :returns: list of domain tuples
        """
        domain = [
            ('product_id', '=', product_id),
            ('available_quantity', '>', 0),
        ]
        if company_id:
            domain.append(('company_id', '=', company_id))
        if location_id:
            domain.append(('location_id', '=', location_id))
        else:
            domain.append(('location_id.usage', '=', 'internal'))
        return domain

    @api.model
    def get_non_expired_available_quants(self, product_id, location_id=None, company_id=None):
        """Return stock.quant recordset of non-expired lots with available stock > 0.

        Availability filtering (available_quantity > 0) is handled at the domain/DB level.
        This method additionally filters out expired lots. Use for the public batch-availability API.

        :param product_id: ID of the product.product record
        :param location_id: Optional ID of a specific stock.location.
                            If None, searches all internal locations.
        :param company_id: Optional ID of a res.company record.
                           If provided, filters quants by company.
        :returns: Filtered stock.quant recordset
        """
        domain = self._build_quant_domain(product_id, location_id, company_id=company_id)
        quants = self.env['stock.quant'].search(domain)
        now = fields.Datetime.now()

        return quants.filtered(
            lambda q: q.available_quantity > 0 and (not q.lot_id or not q.lot_id.expiration_date or q.lot_id.expiration_date > now)
        )

    @api.model
    def get_non_expired_quants_raw(self, product_id, location_id=None):
        """Return stock.quant recordset of non-expired lots with quantity > 0 (no reservation filter).

        Does NOT filter by reserved_quantity. Use this when the caller applies its own
        availability logic (e.g. encounter-level allocation deductions in OrderSaveService).

        :param product_id: ID of the product.product record
        :param location_id: Optional ID of a specific stock.location.
                            If None, searches all internal locations.
        :returns: Filtered stock.quant recordset
        """
        domain = self._build_quant_domain(product_id, location_id)
        quants = self.env['stock.quant'].search(domain)
        now = fields.Datetime.now()

        return quants.filtered(
            lambda q: not q.lot_id or not q.lot_id.expiration_date or q.lot_id.expiration_date > now
        )

    @api.model
    def get_available_batches(self, product_uuid, company_id=None):
        """Return non-expired, available-stock lot/batch data for the given product UUID.

        Batches are sorted by expiry date ascending (soonest expiry first);
        batches with no expiry date appear at the end.
        Manufacturer name is included if set on the product.

        :param product_uuid: UUID of the product.product record
        :param company_id: Optional ID of a res.company record.
                           If provided, filters quants by company for efficient querying.
        """
        product = self.env['product.product'].search(
            [('uuid', '=', product_uuid)], limit=1
        )
        if not product:
            raise ValueError("No product found for UUID: %s" % product_uuid)

        quants = self.get_non_expired_available_quants(product.id, company_id=company_id)

        # Prime the prefetch cache to avoid N+1 ORM reads
        quants.mapped('lot_id')
        quants.mapped('product_id')
        quants.mapped('location_id')
        quants.mapped('company_id')

        # Sort: soonest expiry first; quants with no expiry date go last
        sorted_quants = sorted(
            quants,
            key=lambda q: q.lot_id.expiration_date if (q.lot_id and q.lot_id.expiration_date) else datetime.max
        )
        manufacturer = product.product_tmpl_id.manufacturer
        result = []
        for quant in sorted_quants:
            entry = {
                'stock_location_name': quant.location_id.name,
                'available_quantity': quant.available_quantity,
                'on_hand_quantity': quant.quantity,
                'unit': quant.product_uom_id.name if quant.product_uom_id else None,
            }
            if quant.lot_id:
                entry['batch_number'] = quant.lot_id.name
                if quant.lot_id.expiration_date:
                    entry['expiry_date'] = quant.lot_id.expiration_date.isoformat() + 'Z'
            if manufacturer:
                entry['manufacturer'] = manufacturer.name
            result.append(entry)

        return result
