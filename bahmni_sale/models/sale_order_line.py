from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF, float_is_zero

from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round


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
    
    
    @api.onchange('product_uom_qty')
    def onchange_product_uom_qty(self):
        if self.product_uom_qty:           
            if bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_sale.sale_price_markup')) == True:
                self.price_unit = self.lot_id.sale_price if self.lot_id.sale_price > 0.0 else self.product_id.lst_price 
            

    
    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            self.expiry_date = self.lot_id.expiration_date             
            if bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_sale.sale_price_markup')) == True:
                self.price_unit = self.lot_id.sale_price if self.lot_id.sale_price > 0.0 else self.product_id.lst_price 
            
                
    @api.onchange('product_id')
    def onchange_product_id_inherit(self):
        if self.product_id:           
           self.lot_id = self.get_available_batch_details(self.product_id,self.order_id.id)
           
    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            if line.qty_invoiced > 0:
                continue
            if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
                line.price_unit = 0.0
            else:
                price = line.with_company(line.company_id)._get_display_price()
                if bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_sale.sale_price_markup')) == True:
                    price = line.lot_id.sale_price if line.lot_id.sale_price > 0.0 else line.product_id.lst_price
                line.price_unit = line.product_id._get_tax_included_unit_price(
                    line.company_id,
                    line.order_id.currency_id,
                    line.order_id.date_order,
                    'sale',
                    fiscal_position=line.order_id.fiscal_position_id,
                    product_price_unit=price,
                    product_currency=line.currency_id
                )
    
           

    @api.model
    def get_available_batch_details(self, product_id, sale_order):
        context = self._context.copy() or {}
        sale_order = self.env['sale.order'].browse(sale_order)
        context['location_id'] = sale_order.location_id and sale_order.location_id.id or False
        context['search_in_child'] = True
        shop_location_id = sale_order.shop_id.location_id.id if sale_order.shop_id.location_id.id else self.order_id.shop_id.location_id.id
        stock_quant_lot = self.env['stock.quant'].search([
        ('product_id','=', product_id.id if type(product_id) != list else product_id[0]),
        ('location_id', '=', shop_location_id),
        ('quantity', '>' , 0)])
        stock_prod_lot = self.env['stock.lot'].search([('id', 'in', [lot_id.lot_id.id for lot_id in stock_quant_lot])])
        already_used_batch_ids = []
        for line in sale_order.order_line:
            if line.lot_id:
                id = line.lot_id.id
                already_used_batch_ids.append(id.__str__())
        query = ['&', ('product_id', '=', product_id.id if type(product_id) != list else product_id[0]), 
                ('id', 'in', [lot_id.lot_id.id for lot_id in stock_quant_lot]),
                 ('id', 'not in', already_used_batch_ids if already_used_batch_ids else False)]\
                 if len(already_used_batch_ids) > 0 else [('id', 'in', [lot_id.lot_id.id for lot_id in stock_quant_lot]),('product_id','=', product_id.id if type(product_id) != list else product_id[0])]
                 
        for prodlot in stock_prod_lot.search(query, order='expiration_date asc'):   
            if prodlot.expiration_date and prodlot.product_qty > 0:        
                date_lenth = len(str(prodlot.expiration_date))            
                if len(str(prodlot.expiration_date)) > 20:                
                    formatted_ts = datetime.strptime(str(prodlot.expiration_date), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")
                else:                
                    formatted_ts = datetime.strptime(str(prodlot.expiration_date), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                if(formatted_ts and datetime.strptime(str(formatted_ts), DTF) > datetime.today()):
                    return prodlot
            elif prodlot.product_qty > 0:
                return prodlot
            else:
                pass
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
                
    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        
        print("self.display_type",self.display_type)
        
        
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [Command.set(self.tax_id.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
            'lot_id':self.lot_id.id,
            'expiry_date': self.expiry_date,
        }
        analytic_account_id = self.order_id.analytic_account_id.id
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
            if 'analytic_distribution' in res:
                res['analytic_distribution'][analytic_account_id] = res['analytic_distribution'].get(analytic_account_id, 0) + 100
            else:
                res['analytic_distribution'] = {analytic_account_id: 100}
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res
