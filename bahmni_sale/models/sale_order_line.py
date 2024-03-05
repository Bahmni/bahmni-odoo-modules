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
            res_config = self.env['res.config.settings'].search([],order='id desc',limit=1)
            
            if res_config.sale_price_markup == True:
                self.price_unit = self.lot_id.sale_price if self.lot_id.sale_price > 0.0 else self.product_id.lst_price 
            else:
                self.price_unit = self.product_id.lst_price 

    
    @api.onchange('lot_id')
    def onchange_lot_id(self):
        if self.lot_id:
            self.expiry_date = self.lot_id.expiration_date 
            res_config = self.env['res.config.settings'].search([],order='id desc',limit=1)
            
            print("res_config",res_config.id)
            print("res_config",res_config.sale_price_markup)
               
            
            if res_config.sale_price_markup == True:
                self.price_unit = self.lot_id.sale_price if self.lot_id.sale_price > 0.0 else self.product_id.lst_price 
            else:
                self.price_unit = self.product_id.lst_price 
                
    @api.onchange('product_id')
    def onchange_product_id_inherit(self):
        if self.product_id:
           self.price_unit = self.product_id.lst_price
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
            date_lenth = len(str(prodlot.expiration_date))            
            if len(str(prodlot.expiration_date)) > 20:                
                formatted_ts = datetime.strptime(str(prodlot.expiration_date), "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M:%S")
            else:                
                formatted_ts = datetime.strptime(str(prodlot.expiration_date), "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            if(formatted_ts and datetime.strptime(str(formatted_ts), DTF) > datetime.today()):
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
