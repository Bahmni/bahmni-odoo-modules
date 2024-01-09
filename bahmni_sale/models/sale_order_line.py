from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    external_id = fields.Char(string="External ID",
                              help="This field is used to store encounter ID of bahmni api call")
    external_order_id = fields.Char(string="External Order ID",
                                    help="This field stores the order ID got from api call.")
    order_uuid = fields.Char(string="Order UUID",
                             help="Field for generating a random unique ID.")
    dispensed = fields.Boolean(string="Dispensed",
                               help="Flag to identify whether drug order is dispensed or not.")
    lot_id = fields.Many2one('stock.lot', string="Batch No")
    expiry_date = fields.Datetime(string="Expiry date")

    product_uom_qty = fields.Float(
        string="Quantity",
        compute='_compute_product_uom_qty',
        digits='Product Unit of Measure', default=0.0,
        store=True, readonly=False, required=True, precompute=True)
    
    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            self.expiry_date = self.lot_id.expiration_date
            sale_price_basedon_cost_price_markup = '0'
            if sale_price_basedon_cost_price_markup == '1':
                self.price_unit = self.lot_id.sale_price if self.lot_id.sale_price > 0.0 else self.price_unit
                
    @api.onchange('product_id')
    def onchange_product_id_inherit(self):
        if self.product_id:
           self.lot_id = self.get_available_batch_details(self.product_id,self.order_id.id)

    @api.model
    def get_available_batch_details(self, product_id, sale_order):
        context = self._context.copy() or {}
        sale_order = self.env['sale.order'].browse(sale_order)
        context['location_id'] = sale_order.location_id and sale_order.location_id.id or False
        context['search_in_child'] = True
        stock_prod_lot = self.env['stock.lot'].search([('product_id','=', product_id.id if type(product_id) != list else product_id[0])])

        already_used_batch_ids = []
        for line in sale_order.order_line:
            if line.lot_id:
                id = line.lot_id.id
                already_used_batch_ids.append(id.__str__())
        query = ['&', ('product_id', '=', product_id.id if type(product_id) != list else product_id[0]), 
                 ('id', 'not in', already_used_batch_ids if already_used_batch_ids else False)]\
                 if len(already_used_batch_ids) > 0 else [('product_id','=', product_id.id if type(product_id) != list else product_id[0])]
                 
        for prodlot in stock_prod_lot.search(query, order='expiration_date asc'):
            if(prodlot.expiration_date and datetime.strptime(str(prodlot.expiration_date), DTF) > datetime.today()):
                return prodlot
        return None
    
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).
 
        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 
                             'sale_line_ids': [(6, 0, [line.id])],
                             'lot_id': line.lot_id.id,
                             'expiry_date': line.expiry_date})
                self.env['account.invoice.line'].create(vals)
