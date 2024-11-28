# -*- coding: utf-8 -*-

import time
from datetime import timedelta, datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

RES_USERS = 'res.users'
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

CUSTOM_STATUS = [
		('draft', 'Draft'),
		('confirm', 'Confirmed')]

ENTRY_MODE =  [('manual','Manual'),
			   ('auto', 'Auto')]

class BahmniCustomerReturn(models.Model):
	_name = 'bahmni.customer.return'
	_description = 'Customer Sales Return'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
	_order = 'entry_date desc'

	
	name = fields.Char(string="Return No")
	entry_date = fields.Datetime('Entry Date',default=fields.Datetime.now)
	location_id = fields.Many2one('stock.location', 'Return Location',domain=[('active', '=', True),('usage', '=', 'internal')])
	customer_id = fields.Many2one('res.partner', 'Customer',domain=[('active', '=', True),('customer_rank', '>', 0)])
	
	status = fields.Selection(selection=CUSTOM_STATUS, string="Status", copy=False, default="draft", readonly=True, store=True, tracking=True)
	remarks = fields.Text(string="Remarks", copy=False)
	company_id = fields.Many2one('res.company', copy=False, default=lambda self: self.env.company, ondelete='restrict', readonly=True, required=True)
	currency_id = fields.Many2one('res.currency', string="Currency", copy=False, default=lambda self: self.env.company.currency_id.id, ondelete='restrict', readonly=True, tracking=True)
	
	tot_amt = fields.Float(string="Return Amount", store=True, compute='_compute_all_line')
	product_ids = fields.Many2many('product.product','customer_returns_products','return_id','product_id','Products',domain=[('active', '=', True),('type','=','product')])
	
	
	active = fields.Boolean(string="Visible", default=True)
	entry_mode = fields.Selection(selection=ENTRY_MODE, string="Entry Mode", copy=False, default="manual", tracking=True, readonly=True)
	crt_date = fields.Datetime(string="Creation Date", copy=False, default=fields.Datetime.now, readonly=True)
	user_id = fields.Many2one(RES_USERS, string="Created By", copy=False, default=lambda self: self.env.user.id, ondelete='restrict', readonly=True)
	confirm_date = fields.Datetime(string="Comfirmed Date", copy=False, readonly=True)
	confirm_user_id = fields.Many2one(RES_USERS, string="Comfirmed By", copy=False, ondelete='restrict', readonly=True)
	update_date = fields.Datetime(string="Last Updated Date", copy=False, readonly=True)
	update_user_id = fields.Many2one(RES_USERS, string="Last Updated By", copy=False, ondelete='restrict', readonly=True)
	
	
	line_ids = fields.One2many('bahmni.customer.return.line', 'header_id', string="Return Details", copy=True)

	@api.onchange('product_ids')
	def onchange_product_ids(self):
		if self.product_ids:
			now = datetime.now()
			threshold_days = int(self.env['ir.config_parameter'].sudo().get_param('bahmni_auto_customer_return.no_of_days_threshold'))
			date_threshold = now - timedelta(days=threshold_days) 

			# Get the currently selected product IDs
			selected_product_ids = self.product_ids.ids

			# Get product IDs already present in the lines
			existing_product_ids = self.line_ids.mapped('product_id.id')

			# Determine newly added product IDs
			new_product_ids = list(set(selected_product_ids) - set(existing_product_ids))

			# Fetch sale order lines for the newly added products
			sale_order_lines = self.env['sale.order.line'].search([
				('order_partner_id', '=', self.customer_id.id),
				('product_id', 'in', new_product_ids),
				('order_id.date_order', '>=', date_threshold)
			])

			# Get products without matching sale orders
			products_without_sales = self.env['product.product'].browse(new_product_ids).filtered(
				lambda product: product.id not in sale_order_lines.mapped('product_id.id')
			)

			if products_without_sales:
				# Generate error message for products without sales
				product_names = ', '.join(products_without_sales.mapped('name'))
				raise UserError(f"{product_names} have no sale orders in the last {threshold_days} days")

			# Remove lines for products no longer selected
			self.line_ids = self.line_ids.filtered(lambda line: line.product_id.id in selected_product_ids)

			# Add new lines for products not already in `line_ids`
			for line in sale_order_lines:
				if line.product_id.id not in existing_product_ids:
					self.line_ids = [(0, 0, {
						'header_id': self.id,
						'product_id': line.product_id.id,
						'order_qty': line.product_uom_qty,
						'uom_id': line.product_uom.id,
						'lot_id': line.lot_id.id if line.lot_id else False,
						'expiry_date': line.expiry_date,
						'unit_price': line.price_unit,
						'sale_date': line.order_id.date_order,
						'sale_order_ref': line.order_id.name,
						'sale_order_id': line.order_id.id,
						'sale_order_line_id': line.id,
					})]
		else:
			# If no products are selected, clear all lines
			self.line_ids = [(5, 0, 0)]

	
	@api.depends('line_ids')
	def _compute_all_line(self):
		for data in self:
			data.tot_amt = sum(line.sub_total for line in data.line_ids)          
	
	
	def display_warnings(self, warning_msg, kw):
		if warning_msg:
			formatted_messages = "\n".join(warning_msg)
			if not kw.get('mode_of_call'):
				raise UserError(_(formatted_messages))
			else:
				return [formatted_messages]
		else:
			return False
	
	def validate_detail_lines(self, detail_line, warning_msg):
		if detail_line.qty <= 0:
			warning_msg.append(f"({detail_line.product_id.name}) return quantity should be greater than zero")
		if detail_line.unit_price <= 0:
			warning_msg.append(f"({detail_line.product_id.name}) unit price should be greater than zero")
		if detail_line.qty > detail_line.order_qty:
			warning_msg.append(f"({detail_line.description}) quantity cannot be greater than the ordered quantity")
	
	def validate_line_items(self, warning_msg):
		if not self.line_ids:
			warning_msg.append("System not allow to confirm with empty line details")
		else:
			for detail_line in self.line_ids:
				self.validate_detail_lines(detail_line, warning_msg)
	
	def validations(self, **kw):
		warning_msg = []
		if self.status in ('draft'):
			self.validate_line_items(warning_msg)        

		return self.display_warnings(warning_msg, kw)
	
	
	def entry_confirm(self):
		if self.status in ('draft'):
			self.validations()
			self.name = self.env['ir.sequence'].next_by_code('bahmni.customer.return.sequence') or 'New'
			self.write({'status': 'confirm',
						'confirm_user_id': self.env.user.id,
						'confirm_date': time.strftime(TIME_FORMAT)
						})
		return True
	
	def unlink(self):
		for rec in self:
			if rec.status != 'draft':
				raise UserError(_("You can't delete confirmed entries"))
			models.Model.unlink(rec)
		return True
	
	def write(self, vals):
		vals.update({'update_date': time.strftime(TIME_FORMAT),
					 'update_user_id': self.env.user.id})
		return super(BahmniCustomerReturn, self).write(vals)
