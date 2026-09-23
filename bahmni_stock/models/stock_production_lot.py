# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import fields, models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.lot'

    def _compute_display_name(self):
        '''_compute_display_name is used in Odoo 19 to view expiry date in lot display name'''
        for record in self:
            name = record.name or ''
            expiry = ""
            if record.expiration_date:
                expiry = record.expiration_date.strftime("%b %d,%Y")

            if self.env.context.get('parent_shop_id'):
                shop_id = self.env['sale.shop'].search([('id', '=', self.env.context.get('parent_shop_id'))], limit=1)
                stock_quant_lot = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_id.id),
                    ('lot_id', '=', record.id),
                    ('location_id', '=', shop_id.location_id.id),
                    ('quantity', '>', 0)
                ], limit=1)
                if stock_quant_lot and expiry:
                    name = "%s [%s], %s" % (name, expiry, stock_quant_lot.quantity)
            elif self.env.context.get('default_internal_location_id'):
                stock_quant_lot = self.env['stock.quant'].search([
                    ('product_id', '=', record.product_id.id),
                    ('lot_id', '=', record.id),
                    ('location_id', '=', self.env.context.get('default_internal_location_id')),
                    ('quantity', '>', 0)
                ], limit=1)
                if stock_quant_lot and expiry:
                    name = "%s [%s], %s" % (name, expiry, stock_quant_lot.quantity)
            else:
                if expiry:
                    name = "%s [%s]" % (name, expiry)
            record.display_name = name

    @api.depends('product_id')
    def _get_future_stock_forecast(self):
        """ Gets stock of products for locations """
        for lot in self:
            context = self.env.context
            if 'location_id' not in context or context['location_id'] is None:
                locations = self.env['stock.location'].search([('usage', '=', 'internal')])
            elif context.get('search_in_child', False):
                locations = self.env['stock.location'].search([('location_id', 'child_of', context['location_id'])]) or [context['location_id']]
            else:
                locations = self.env['stock.lot'].browse(context.get('location_id', 15))
            if locations and locations[0]:
                self._cr.execute('''select
                                        lot_id,
                                        sum(quantity)
                                    from
                                        stock_quant
                                    where
                                        location_id IN %s and lot_id = %s
                                    group by lot_id''',
                                 (tuple(locations.ids), lot.id,))
                result = self._cr.dictfetchall()
                if result and result[0]:
                    lot.stock_forecast = result[0].get('sum')

                    product_uom_id = context.get('product_uom', None)
                    if product_uom_id:
                        product_uom = self.env['uom.uom'].browse(product_uom_id)
                        lot.stock_forecast = result[0].get('sum') * product_uom.factor

    sale_price = fields.Float(string="Sale Price", digits='Product Price')
    mrp = fields.Float(string="MRP", digits='Product Price')
    cost_price = fields.Float(string="Cost Price", digits='Product Price')
    stock_forecast = fields.Float(
        string="Available forecast",
        compute=_get_future_stock_forecast,
        store=True,
        digits='Product Unit of Measure',
        help="Future stock forecast quantity of products with this Serial Number available in company warehouses",
    )