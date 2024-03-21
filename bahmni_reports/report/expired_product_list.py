from odoo import models, fields, api
import time
from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
try:
	from odoo.tools.misc import xlsxwriter
except ImportError:
	import xlsxwriter
import io
import json
from odoo.tools import date_utils

class ExpiredProductList(models.Model):   
	_name = 'expired.product.list'
	
	name = fields.Char(string="Report Name" , default='Expired Product List')
	from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
	to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
	product_id = fields.Many2many('product.product','expired_product_reports','reports_id','product_id','Product Name',domain=[('active', '=', True),('type','=','product')])
	location_id = fields.Many2one('stock.location', 'Location Name',domain=[('active', '=', True),('usage', '=', 'internal')])  
	
	generate_date = fields.Datetime('Generate Date', default=time.strftime('%Y-%m-%d %H:%M:%S'), readonly=True)
	generate_user_id = fields.Many2one('res.users', 'Generate By', default=lambda self: self.env.user.id, readonly=True)    
   
	
	@api.onchange('from_date', 'to_date')
	def onchange_date_validations(self):
		if self.from_date > self.to_date:
		   raise UserError(_("Kindly choose correct from & to date."))
	
	def print_report(self):
		for rec in self:
			data = {                
				'self_rec': rec.id,
			}
			return {
				'type': 'ir.actions.report',
				'data': {'model': 'expired.product.list',
						 'options': json.dumps(data,
											   default=date_utils.json_default),
						 'output_format': 'xlsx',
						 'report_name': 'Expired_Product_List',
						 },
				'report_type': 'stock_xlsx',
			}
	
	def get_xlsx_report(self, data, response):
		"""this is used to print the report of all records"""        
		
		rec_obj = self.env['expired.product.list'].search([('id', '=', data['self_rec'])])
		current_datetime = datetime.now() + timedelta(hours=5, minutes=30)
		
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {'in_memory': True})
		sheet = workbook.add_worksheet()
		
		# Formats
		format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'border': 1})
		format2 = workbook.add_format({'font_size': 11, 'bold': True, 'border': 1, 'bg_color': '#a5f9f7'})   
		format2.set_align('center')        
		format11 = workbook.add_format({'font_size': 11, 'bold': True, 'border': 1, 'font_name': 'Calibri',})
		format11_a = workbook.add_format({'font_size': 11,'align': 'center', 'bold': True, 'border': 1, 'font_name': 'Calibri',})
		format11_b = workbook.add_format({'font_size': 11,'align': 'right', 'bold': True, 'border': 1, 'font_name': 'Calibri',})
		format12 = workbook.add_format({'font_size': 10, 'font_name': 'Calibri', 'border': 1})
		format12_a = workbook.add_format({'font_size': 10, 'align': 'center','font_name': 'Calibri', 'border': 1})
		format12_b = workbook.add_format({'font_size': 10, 'align': 'right', 'border': 1,'font_name': 'Calibri'})
		
		product_list = []        
		if len(rec_obj.product_id) == 0:
			product_names = 'All'
		elif len(rec_obj.product_id) <= 3:
			for product in rec_obj.product_id:
				product_list.append(product.name)
			product_names = ', '.join(product_list)
		else:
			product_names = 'Limited'
		
		sheet.merge_range(0, 0, 0, 9,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
		sheet.merge_range(1, 0, 1, 9,'Expired Product List', format1)
		sheet.merge_range(2, 0, 2, 5,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
		sheet.merge_range(2, 6, 2, 9,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)
		
		sheet.merge_range(3, 0, 3, 5,"Location Name : "+ str(rec_obj.location_id.complete_name), format11)
		sheet.merge_range(3, 6, 3, 9,"Product : "+product_names, format11)
		
		sheet.merge_range(4, 0, 4, 5,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)       
		
		sheet.merge_range(4, 6, 4, 9,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 
		
	   
 
		sheet.write(6, 0, "S.No", format2)
		sheet.set_column('A:A', 5)
		sheet.write(6, 1, "Serial Number", format2)
		sheet.set_column('B:B', 20)
		sheet.write(6, 2, "Product Name", format2)
		sheet.set_column('C:C', 25)
		sheet.write(6, 3, "Product Category", format2)
		sheet.set_column('D:D', 18)
		sheet.write(6, 4, "UOM", format2)
		sheet.set_column('E:E', 10)
		sheet.write(6, 5, "Qty", format2)
		sheet.set_column('F:F', 8)
		sheet.write(6, 6, "Cost Price", format2)
		sheet.set_column('G:G', 15)
		sheet.write(6, 7, "Total Value", format2)
		sheet.set_column('H:H', 16)       
		sheet.write(6, 8, "Expired Date", format2)
		sheet.set_column('I:I', 16)
		sheet.write(6, 9, "Stock Location", format2)
		sheet.set_column('J:J', 16)
		
		if rec_obj.product_id:
			lot_data_obj = self.env['stock.quant'].search([('lot_id', '!=', False),('location_id', '=', rec_obj.location_id.id),('removal_date', '>=', rec_obj.from_date), ('removal_date', '<=', rec_obj.to_date),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'product_id desc' )
		else:
			lot_data_obj = self.env['stock.quant'].search([('lot_id', '!=', False), ('location_id', '=', rec_obj.location_id.id),('removal_date', '>=', rec_obj.from_date), ('removal_date', '<=', rec_obj.to_date)], order = 'product_id desc' )
		
		row_num = 7
		s_no = 1            
		total_val =0
		
		for data in sorted(lot_data_obj, key=lambda x: x.product_id.product_tmpl_id.name,reverse=False):           
		   
			
			sheet.write(row_num, 0, s_no, format12_a)
			sheet.write(row_num, 1, data.lot_id.name, format12)
			sheet.write(row_num, 2, data.product_id.product_tmpl_id.name, format12)
			sheet.write(row_num, 3, data.product_id.categ_id.name, format12)
			sheet.write(row_num, 4, data.product_id.uom_id.name, format12)
			sheet.write(row_num, 5, "{:.2f}".format(data.quantity), format12_b)
			sheet.write(row_num, 6, "{:.2f}".format(data.lot_id.cost_price), format12_b)
			sheet.write(row_num, 7, "{:.2f}".format((data.quantity * data.lot_id.cost_price)), format12_b)
			sheet.write(row_num, 8, ((data.lot_id.expiration_date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")), format12)
			sheet.write(row_num, 9, rec_obj.location_id.complete_name, format12)                
			
			row_num += 1
			total_val += (data.quantity * data.lot_id.cost_price)
			s_no += 1
			
		
		sheet.merge_range(row_num+2, 0, row_num+2, 6,"Grand Total", format11_a)
		sheet.write(row_num+2, 7, "{:.2f}".format(total_val), format11_b)
			
		workbook.close()
		output.seek(0)
		response.stream.write(output.read())
		output.close()     
	
