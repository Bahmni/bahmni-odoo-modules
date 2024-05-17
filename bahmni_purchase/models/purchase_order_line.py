from datetime import datetime
from odoo import models, fields, api
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    mrp = fields.Float(string="MRP")
    manufacturer = fields.Many2one('res.partner', string="Manufacturer",
                                   domain=[('manufacturer', '=', True)])
    prod_categ_id = fields.Many2one('product.category', string='Product Category')

    @api.onchange('product_id')
    def onchange_product_id(self):
        '''Set product category in purchase order line, on change of product_id'''
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if self.product_id:
            self.prod_categ_id = self.product_id.categ_id.id
        return result

    @api.onchange('product_id', 'product_qty', 'product_uom')
    def _onchange_quantity(self):
        '''Method to get mrp for product from vendor configuration in product master'''
        if not self.product_id or not self.product_uom:
            self.mrp = 0
            return

        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order,
            uom_id=self.product_uom)
        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DTF)

        if not seller or (seller and seller.mrp == 0):
            mrp = self.product_id.product_tmpl_id.mrp
            if self.product_id.product_tmpl_id.uom_po_id != self.product_uom:
                default_uom = self.product_id.product_tmpl_id.uom_po_id
                mrp = default_uom._compute_price(mrp, self.product_uom)
        else:
            mrp = seller.mrp
            if mrp and self.product_uom and seller.product_uom != self.product_uom:
                mrp = seller.product_uom._compute_price(mrp, self.product_uom)
            if mrp and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
                mrp = seller.currency_id.compute(mrp, self.order_id.currency_id)
        self.manufacturer = seller.manufacturer.id
        self.mrp = mrp
