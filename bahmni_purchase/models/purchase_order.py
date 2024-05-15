from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if bool(self.env['ir.config_parameter'].sudo().get_param(
                'bahmni_purchase.update_product_prices_on_po_confirm')):
            for order in self:
                for line in order.order_line:
                    price_unit, sale_price, mrp = self._calculate_prices(line)
                    self._update_price_for_supplier(line.product_id.product_tmpl_id.id, price_unit, mrp)
                    self._update_price_for_product(line.product_id, price_unit, sale_price, mrp)
        return res

    def _calculate_prices(self, purchase_order_line):
        price_unit = purchase_order_line.price_unit
        mrp = purchase_order_line.mrp
        tax = purchase_order_line.price_tax / purchase_order_line.product_qty if purchase_order_line.product_qty > 0 else purchase_order_line.price_tax
        # Compute the price_unit,mrp for the template's UoM, because the supplier's UoM is related to that UoM.
        if purchase_order_line.product_id.product_tmpl_id.uom_po_id != purchase_order_line.product_uom:
            default_uom = purchase_order_line.product_id.product_tmpl_id.uom_po_id
            price_unit = purchase_order_line.product_uom._compute_price(price_unit, default_uom)
            mrp = purchase_order_line.product_uom._compute_price(mrp, default_uom)
            tax = purchase_order_line.product_uom._compute_price(tax, default_uom)
        total_cost = price_unit + tax
        sale_price = self.env['price.markup.table'].calculate_price_with_markup(total_cost)
        # Set sale_price as none if no markup value is added
        if sale_price == total_cost:
            sale_price = None
        return price_unit, sale_price, mrp

    def _update_price_for_product(self, product_id, price_unit, sale_price, mrp):
        if sale_price:
            product_id.write({'standard_price': price_unit, 'list_price': sale_price, 'mrp': mrp})
        else:
            product_id.write({'standard_price': price_unit, 'mrp': mrp})

    def _update_price_for_supplier(self, product_tmpl_id, price_unit, mrp):
        seller_info = self.env['product.supplierinfo'].search([('partner_id', '=', self.partner_id.id),
                                                               ('product_tmpl_id', '=', product_tmpl_id)])
        seller_info.mrp = mrp
        seller_info.price = price_unit
