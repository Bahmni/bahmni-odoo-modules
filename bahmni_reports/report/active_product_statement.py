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
from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ActiveProductStatement(models.Model):   
	_name = 'active.product.statement'

	name = fields.Char(string="Report Name" , default='Active Product Statement')
	from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
	to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
	product_id = fields.Many2many('product.product','active_product_statement_product_reports','reports_id','product_id','Product Name',domain=[('active', '=', True),('type','=','product')])
	
	generate_date = fields.Datetime('Generate Date', default=time.strftime('%Y-%m-%d %H:%M:%S'), readonly=True)
	generate_user_id = fields.Many2one('res.users', 'Generate By', default=lambda self: self.env.user.id, readonly=True)    
   
   
	@api.onchange('from_date', 'to_date')
	def onchange_date_validations(self):
		if self.from_date < fields.Date.today() or self.to_date < fields.Date.today():
		   raise UserError(_("From date and to date should not be less than today's date."))
		if self.from_date > self.to_date:
		   raise UserError(_("Kindly choose correct from & to date."))
   
	
	def print_report(self):
		for rec in self:
			data = {                
				'self_rec': rec.id,
			}
			return {
				'type': 'ir.actions.report',
				'data': {'model': 'active.product.statement',
						 'options': json.dumps(data,
											   default=date_utils.json_default),
						 'output_format': 'xlsx',
						 'report_name': 'Active_Product_Statement',
						 },
				'report_type': 'stock_xlsx',
			}
	
	def get_xlsx_report(self, data, response):
		"""this is used to print the report of all records"""        
		
		rec_obj = self.env['active.product.statement'].search([('id', '=', data['self_rec'])])
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
		
		sheet.merge_range(0, 0, 0, 8,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
		sheet.merge_range(1, 0, 1, 8,'Active Product Statement', format1)
		sheet.merge_range(2, 0, 2, 4,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
		sheet.merge_range(2, 5, 2, 8,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)
		
		sheet.merge_range(3, 0, 3, 8,"Product : "+product_names, format11)
				
		sheet.merge_range(4, 0, 4, 4,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)          
		sheet.merge_range(4, 5, 4, 8,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 
	   
 
		sheet.write(6, 0, "S.No", format2)
		sheet.set_column('A:A', 5)        
		sheet.write(6, 1, "Product Name", format2)
		sheet.set_column('B:B', 25)         
		sheet.write(6, 2, "Product Category", format2)
		sheet.set_column('C:C', 20)                
		sheet.write(6, 3, "UOM", format2)
		sheet.set_column('D:D', 10)
		sheet.write(6, 4, "Serial Number", format2)
		sheet.set_column('E:E', 18)
		sheet.write(6, 5, "Stock Qty", format2)
		sheet.set_column('F:F', 12)
		sheet.write(6, 6, "Cost Price", format2)
		sheet.set_column('G:G', 12)       
		sheet.write(6, 7, "Total", format2)
		sheet.set_column('H:H', 15)            
		sheet.write(6, 8, "Expiration Date", format2)
		sheet.set_column('I:I', 16)
	   
		
		lot_obj = self.env['stock.lot'].search([
			('expiration_date', '>=', rec_obj.from_date),
			('expiration_date', '<=', rec_obj.to_date),
			('product_id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids),
		], order='product_id desc')
		
		print("lot_objlot_objlot_obj",lot_obj)
		row_num = 7
		s_no = 1            
		total_val =0
		
		for data in sorted(lot_obj, key=lambda x: x.expiration_date,reverse=False):      
			
			sheet.write(row_num, 0, s_no, format12_a)
			sheet.write(row_num, 1, data.product_id.product_tmpl_id.name, format12)
			sheet.write(row_num, 2, data.product_id.categ_id.name, format12)
			sheet.write(row_num, 3, data.product_id.uom_id.name, format12)
			sheet.write(row_num, 4, data.name if data.name else '-', format12)
			sheet.write(row_num, 5, "{:.2f}".format(data.product_qty), format12_b)
			sheet.write(row_num, 6, "{:.2f}".format(data.cost_price), format12_b)
			sheet.write(row_num, 7, "{:.2f}".format((data.product_qty * data.cost_price)), format12_b)           
			sheet.write(row_num, 8, ((data.expiration_date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")), format12)
			row_num += 1
			total_val += (data.product_qty * data.cost_price)
			s_no += 1
			
		
		sheet.merge_range(row_num+2, 0, row_num+2, 6,"Grand Total", format11_a)
		sheet.write(row_num+2, 7, "{:.2f}".format(total_val), format11_b)
			
		workbook.close()
		output.seek(0)
		response.stream.write(output.read())
		output.close()     
	
