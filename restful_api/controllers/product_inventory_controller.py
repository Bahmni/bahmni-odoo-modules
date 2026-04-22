import logging

from odoo import http
from odoo.http import request
from odoo.addons.restful_api.common import (
    invalid_response,
    valid_response,
)

_logger = logging.getLogger(__name__)


class ProductInventoryController(http.Controller):

    @http.route('/api/get-available-stocks', type="http", auth="user", methods=["GET", "OPTIONS"], csrf=True, cors='*')
    def get_available_stocks(self, **kw):
        """GET endpoint returning available stock data for a given product UUID."""
        try:
            product_uuid = kw.get('product_uuid')
            if not product_uuid:
                return invalid_response("bad_request", "product_uuid is required", status=400)

            location_uuid = kw.get('location_uuid')
            company_id = None
            if location_uuid:
                company = request.env['company.location.mapping'].get_company_by_location_uuid(location_uuid)
                if not company:
                    return invalid_response("bad_request", "No company mapping found for location_uuid: %s" % location_uuid, status=400)
                company_id = company.id

            batches = request.env['product.inventory.service'].get_available_batches(product_uuid, company_id=company_id)
            if batches is None:
                return invalid_response("not_found", "No product found for the given UUID", status=404)
            return valid_response(batches)
        except Exception as e:
            _logger.exception("Error in get_available_batches for product_uuid=%s, location_uuid=%s", kw.get('product_uuid'), kw.get('location_uuid'))
            return invalid_response("error", "An internal error occurred.", status=500)
