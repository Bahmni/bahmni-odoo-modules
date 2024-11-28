# -*- coding: utf-8 -*-
import time
from datetime import timedelta, datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from odoo.exceptions import UserError

class BahmniCustomerReturnLine(models.Model):
	_name = 'bahmni.customer.return.line'
	_description = 'Return Details'
	_order = 'id asc'

	header_id = fields.Many2one('bahmni.customer.return', string="Header Ref", index=True, required=True, ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Product Name',domain=[('active', '=', True),('type','=','product')])
	qty = fields.Float(string="Return Qty")
	order_qty = fields.Float(string="Sale Order Qty")
	uom_id = fields.Many2one('uom.uom', string="UOM", ondelete='restrict')	
	lot_id = fields.Many2one('stock.lot', string="Batch No")
	expiry_date = fields.Datetime(string="Expiry Date")
	unit_price = fields.Float(string="Unit Price")
	sub_total = fields.Float(string="Sub Total")    
	sale_date = fields.Date('Sale Date') 
	sale_order_ref = fields.Char(string="Sale Order Ref")
	sale_order_id = fields.Many2one('sale.order', string="Sale Order")
	sale_order_line_id = fields.Many2one('sale.order.line', string="Sale Order Line")
	company_id = fields.Many2one('res.company', copy=False, default=lambda self: self.env.company, ondelete='restrict', readonly=True, required=True)
	
				
	@api.onchange('qty')
	def onchange_qty(self):
		if self.qty:
			if self.qty > self.order_qty:
				raise UserError(_("Return quantity cannot be greater than ordered quantity."))
			self.sub_total = self.qty * self.unit_price 
