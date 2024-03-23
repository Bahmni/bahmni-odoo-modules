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

class SaleDiscountHeadStatement(models.Model):   
	_name = 'sale.discount.head.statement'

	name = fields.Char(string="Report Name" , default='Sales Discount Statement')
	from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
	to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
	report_type = fields.Selection([('summary', 'Discount Head Wise'),('details', 'Customer Wise'),('order', 'Order Wise')], 
				  string='Report Type', widget='selection',default='summary')
	discount_head_id = fields.Many2many('account.account','sale_discount_head_statement_reports','reports_id','discount_id','Discount Head',domain=[('account_type', '=', 'income_other')])
	
	generate_date = fields.Datetime('Generate Date', default=time.strftime('%Y-%m-%d %H:%M:%S'), readonly=True)
	generate_user_id = fields.Many2one('res.users', 'Generate By', default=lambda self: self.env.user.id, readonly=True)    
   
   
	@api.onchange('from_date', 'to_date')
	def onchange_date_validations(self):
		if self.from_date > fields.Date.today() or self.to_date > fields.Date.today():
		   raise UserError(_("Future date is not allowed. Kindly choose correct from & to date."))
   
	
	def print_report(self):
		for rec in self:
			data = {                
				'self_rec': rec.id,
			}
			if rec.report_type == 'summary':
				return {
					'type': 'ir.actions.report',
					'data': {'model': 'sale.discount.head.statement',
							 'options': json.dumps(data,
												   default=date_utils.json_default),
							 'output_format': 'xlsx',
							 'report_name': 'Discount_Head_Statement_Summary',
							 },
					'report_type': 'stock_xlsx',
				}
				
			elif rec.report_type == 'order':
				return {
					'type': 'ir.actions.report',
					'data': {'model': 'sale.discount.head.statement',
							 'options': json.dumps(data,
												   default=date_utils.json_default),
							 'output_format': 'xlsx',
							 'report_name': 'Discount_Head_Statement_Order',
							 },
					'report_type': 'stock_xlsx',
				}
			
			else:
				return {
					'type': 'ir.actions.report',
					'data': {'model': 'sale.discount.head.statement',
							 'options': json.dumps(data,
												   default=date_utils.json_default),
							 'output_format': 'xlsx',
							 'report_name': 'Discount_Head_Statement_Details',
							 },
					'report_type': 'stock_xlsx',
				}
	
	def get_xlsx_report(self, data, response):
		"""this is used to print the report of all records"""        
		
		rec_obj = self.env['sale.discount.head.statement'].search([('id', '=', data['self_rec'])])
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
		
		
		if rec_obj.report_type == 'summary':
		
			sheet.merge_range(0, 0, 0, 3,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
			sheet.merge_range(1, 0, 1, 3,'Sales Discount Statement - Discount Head Wise', format1)
			sheet.merge_range(2, 0, 2, 1,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
			sheet.merge_range(2, 2, 2, 3,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)  
					
			sheet.merge_range(3, 0, 3, 1,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)          
			sheet.merge_range(3, 2, 3, 3,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 		   
	 
			sheet.write(5, 0, "S.No", format2)
			sheet.set_column('A:A', 10)        
			sheet.write(5, 1, "Discount Head ", format2)
			sheet.set_column('B:B', 25)         
			sheet.write(5, 2, "No.of Bills", format2)
			sheet.set_column('C:C', 20)                
			sheet.write(5, 3, "Total Value", format2)
			sheet.set_column('D:D', 23) 
			
			self._cr.execute("""
					select acc.code,acc.name,count(sale.id),sum(sale.discount) from sale_order sale 
					left join account_account acc on (acc.id = sale.disc_acc_id)
					where sale.date_order::date >= '%s' and sale.date_order::date <= '%s'
					and state != 'draft' 
					and 
					case
					when (select discount_id from sale_discount_head_statement_reports where reports_id =%s  limit 1) is not null then
					sale.disc_acc_id in (select discount_id from sale_discount_head_statement_reports where reports_id = %s)
					else
					sale.disc_acc_id in (select id from account_account where account_type in ('income_other')) end
					group by 1,2
				"""%(rec_obj.from_date,rec_obj.to_date,rec_obj.id,rec_obj.id))
			sale_discount_data = self._cr.fetchall()         
			
			row_num = 6
			s_no = 1            
			total_val =0			
			
			for data in sale_discount_data: 			    
				
				sheet.write(row_num, 0, s_no, format12_a)
				sheet.write(row_num, 1, data[1], format12)
				sheet.write(row_num, 2, data[2], format12_a)
				sheet.write(row_num, 3, "{:.2f}".format(data[3]), format12_b)			   
				row_num += 1
				total_val += (data[3])
				s_no += 1		
			
			sheet.merge_range(row_num+2, 0, row_num+2, 2,"Grand Total", format11_a)
			sheet.write(row_num+2, 3, "{:.2f}".format(total_val), format11_b)
		
		elif rec_obj.report_type == 'order':
			
			sheet.merge_range(0, 0, 0, 7,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
			sheet.merge_range(1, 0, 1, 7,'Sales Discount Statement - Order Wise', format1)
			sheet.merge_range(2, 0, 2, 2,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
			sheet.merge_range(2, 3, 2, 7,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)  
					
			sheet.merge_range(3, 0, 3, 2,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)          
			sheet.merge_range(3, 3, 3, 7,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11)	   
	 
			sheet.write(5, 0, "S.No", format2)
			sheet.set_column('A:A', 5) 
			sheet.write(5, 1, "Order No. ", format2)
			sheet.set_column('B:B', 25) 
			sheet.write(5, 2, "Order Date ", format2)
			sheet.set_column('C:C', 25)        
			sheet.write(5, 3, "Discount Head ", format2)
			sheet.set_column('D:D', 25)    
			sheet.write(5, 4, "Customer Name ", format2)
			sheet.set_column('E:E', 25) 
			sheet.write(5, 5, "Customer ID ", format2)
			sheet.set_column('F:F', 20)      
			sheet.write(5, 6, "Total Order Value", format2)
			sheet.set_column('G:G', 25)                
			sheet.write(5, 7, "Total Discount Value", format2)
			sheet.set_column('H:H', 20) 
			
			self._cr.execute("""
					select acc.code,acc.name,part.name,part.ref,
					sale.name as order_no,
					to_char(sale.date_order::date,'dd/mm/YYYY') as date,
					sum(amount_total) as total_order,sum(sale.discount) as total_discount from sale_order sale 
					left join account_account acc on (acc.id = sale.disc_acc_id)
					left join res_partner part on (part.id = sale.partner_id)
					where sale.date_order::date >= '%s' and sale.date_order::date <= '%s'
					and state != 'draft' 
					and 
					case
					when (select discount_id from sale_discount_head_statement_reports where reports_id = %s  limit 1) is not null then
					sale.disc_acc_id in (select discount_id from sale_discount_head_statement_reports where reports_id = %s)
					else
					sale.disc_acc_id in (select id from account_account where account_type in ('income_other')) end
					group by 1,2,3,4,5,6
					order by sale.name
				"""%(rec_obj.from_date,rec_obj.to_date,rec_obj.id,rec_obj.id))

			sale_discount_data = self._cr.fetchall()         
			
			row_num = 6
			s_no = 1            
			order_total_val =0
			dis_total_val =0		
			
			for data in sale_discount_data: 								
				sheet.write(row_num, 0, s_no, format12_a)
				sheet.write(row_num, 1, data[4], format12)
				sheet.write(row_num, 2, data[5], format12)
				sheet.write(row_num, 3, data[1], format12)
				sheet.write(row_num, 4, data[2], format12)
				sheet.write(row_num, 5, data[3], format12)
				sheet.write(row_num, 6, "{:.2f}".format(data[6]), format12_b)
				sheet.write(row_num, 7, "{:.2f}".format(data[7]), format12_b)			   
				row_num += 1
				order_total_val += (data[6])
				dis_total_val += (data[7])
				s_no += 1				
			
			sheet.merge_range(row_num+2, 0, row_num+2, 5,"Grand Total", format11_a)
			sheet.write(row_num+2, 6, "{:.2f}".format(order_total_val), format11_b)
			sheet.write(row_num+2, 7, "{:.2f}".format(dis_total_val), format11_b)	
			
			
			
		else:
			
			sheet.merge_range(0, 0, 0, 5,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
			sheet.merge_range(1, 0, 1, 5,'Sales Discount Statement - Customer Wise', format1)
			sheet.merge_range(2, 0, 2, 2,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
			sheet.merge_range(2, 3, 2, 5,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)  
					
			sheet.merge_range(3, 0, 3, 2,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)          
			sheet.merge_range(3, 3, 3, 5,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11)	   
	 
			sheet.write(5, 0, "S.No", format2)
			sheet.set_column('A:A', 5)        
			sheet.write(5, 1, "Discount Head ", format2)
			sheet.set_column('B:B', 25)    
			sheet.write(5, 2, "Customer Name ", format2)
			sheet.set_column('C:C', 25) 
			sheet.write(5, 3, "Customer ID ", format2)
			sheet.set_column('D:D', 25)      
			sheet.write(5, 4, "Total Order Value", format2)
			sheet.set_column('E:E', 20)                
			sheet.write(5, 5, "Total Discount Value", format2)
			sheet.set_column('F:F', 20) 
			
			self._cr.execute("""
					select acc.code,acc.name,part.name,part.ref,sum(amount_total) as total_order,sum(sale.discount) as total_discount from sale_order sale 
					left join account_account acc on (acc.id = sale.disc_acc_id)
					left join res_partner part on (part.id = sale.partner_id)
					where sale.date_order::date >= '%s' and sale.date_order::date <= '%s'
					and state != 'draft' 
					and 
					case
					when (select discount_id from sale_discount_head_statement_reports where reports_id = %s  limit 1) is not null then
					sale.disc_acc_id in (select discount_id from sale_discount_head_statement_reports where reports_id = %s)
					else
					sale.disc_acc_id in (select id from account_account where account_type in ('income_other')) end
					group by 1,2,3,4
				"""%(rec_obj.from_date,rec_obj.to_date,rec_obj.id,rec_obj.id))

			sale_discount_data = self._cr.fetchall()         
			
			row_num = 6
			s_no = 1            
			order_total_val =0
			dis_total_val =0		
			
			for data in sale_discount_data: 								
				sheet.write(row_num, 0, s_no, format12_a)
				sheet.write(row_num, 1, data[1], format12)
				sheet.write(row_num, 2, data[2], format12)
				sheet.write(row_num, 3, data[3], format12)
				sheet.write(row_num, 4, "{:.2f}".format(data[4]), format12_b)
				sheet.write(row_num, 5, "{:.2f}".format(data[5]), format12_b)			   
				row_num += 1
				order_total_val += (data[4])
				dis_total_val += (data[5])
				s_no += 1				
			
			sheet.merge_range(row_num+2, 0, row_num+2, 3,"Grand Total", format11_a)
			sheet.write(row_num+2, 4, "{:.2f}".format(order_total_val), format11_b)
			sheet.write(row_num+2, 5, "{:.2f}".format(dis_total_val), format11_b)		
				
		workbook.close()
		output.seek(0)
		response.stream.write(output.read())
		output.close()     
	
