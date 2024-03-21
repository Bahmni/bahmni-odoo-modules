from odoo import models, fields, api
import time
from datetime import datetime,date, timedelta
from odoo import api, fields, models, _
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import io
import json
from odoo.tools import date_utils

class ProductExpirationRegister(models.Model):
    _name = 'product.expiration.register'
    _order = 'date desc'
    
    name = fields.Char(string="Report Name" , default='Product Expiration Register')
    date = fields.Date('As On Date',required=True,default=lambda * a: time.strftime('%Y-%m-%d'))
    expiry_ageing = fields.Selection([('not_expired','Not Expired'),('expired','Expired'),('expired_30','Expiring in 30 days'),('expired_60','Expiring in 31 - 60 days'),('expired_90','Expiring in 61 - 90 days'),('expired_91','More than 91 days')],'Expiry Ageing',default="not_expired",required=True)
    product_id = fields.Many2many('product.product','pro_exp_reports_new','reports_id','product_id','Drugs Name',domain=[('active', '=', True),('type','=','product')])
    
    generate_date = fields.Datetime('Generate Date', default=time.strftime('%Y-%m-%d %H:%M:%S'), readonly=True)
    generate_user_id = fields.Many2one('res.users', 'Generate By', default=lambda self: self.env.user.id, readonly=True)    
   
    
    def print_report(self):
        for rec in self:
            rec.write({ 'generate_date': time.strftime('%Y-%m-%d %H:%M:%S'),'generate_user_id':self.env.user.id	})
            data = {                
                'self_rec': rec.id,
            }
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'product.expiration.register',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Product_Expiration_Register',
                         },
                'report_type': 'stock_xlsx',
            }
    
    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""        
        
        rec_obj = self.env['product.expiration.register'].search([('id', '=', data['self_rec'])])
        current_datetime = datetime.now() + timedelta(hours=5, minutes=30)
        rec_obj.write({ 'generate_date': time.strftime('%Y-%m-%d %H:%M:%S'),'generate_user_id':self.env.user.id	})
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        
        # Formats
        format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'border': 1})
        format2 = workbook.add_format({'font_size': 11, 'bold': True, 'border': 1, 'bg_color': '#a5f9f7'})   
        format2.set_align('center')        
        format11 = workbook.add_format({'font_size': 11, 'bold': True, 'font_name': 'Calibri', 'border': 1})
        format11_a = workbook.add_format({'font_size': 11,'align': 'center', 'bold': True, 'border': 1, 'font_name': 'Calibri',})
        format11_b = workbook.add_format({'font_size': 11,'align': 'right', 'bold': True, 'border': 1, 'font_name': 'Calibri',})
        format12 = workbook.add_format({'font_size': 10, 'font_name': 'Calibri', 'border': 1})
        format12_a = workbook.add_format({'font_size': 10, 'align': 'center', 'border': 1,'font_name': 'Calibri'})
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
        
        sheet.merge_range(0, 0, 0, 11,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
        sheet.merge_range(1, 0, 1, 11,'Product Expiration Register', format1)
        sheet.merge_range(2, 0, 2, 5,"As On Date : "+ str(rec_obj.date.strftime("%d/%m/%Y")), format11)
        sheet.merge_range(3, 0, 3, 5,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)       
        sheet.merge_range(2, 6, 2, 11,"Drugs : "+product_names, format11)
        sheet.merge_range(3, 6, 3, 11,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11)   
 
        sheet.write(5, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        sheet.write(5, 1, "Serial No", format2)
        sheet.set_column('B:B', 12)
        sheet.write(5, 2, "Product Name", format2)
        sheet.set_column('C:C', 20)
        sheet.write(5, 3, "Qty", format2)
        sheet.set_column('D:D', 7)
        sheet.write(5, 4, "Cost Price", format2)
        sheet.set_column('E:E', 10)
        sheet.write(5, 5, "Creation Date", format2)
        sheet.set_column('F:F', 15)
        sheet.write(5, 6, "Expiration Date", format2)
        sheet.set_column('G:G', 15)
        sheet.write(5, 7, "Expired", format2)
        sheet.set_column('H:H', 9)
        sheet.write(5, 8, "Expiring in 30 days", format2)
        sheet.set_column('I:I', 18)
        sheet.write(5, 9, "Expiring in 31 to 60 days", format2)
        sheet.set_column('J:J', 25)
        sheet.write(5, 10, "Expiring in 61 to 90 days", format2)
        sheet.set_column('K:K', 25)
        sheet.write(5, 11, "More than 91 days", format2)
        sheet.set_column('L:L', 18)
        
        if rec_obj.expiry_ageing=='not_expired':
            if rec_obj.product_id:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'product_id desc' )
            else:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today())], order = 'product_id desc' )
        elif rec_obj.expiry_ageing=='expired':
            if rec_obj.product_id:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '<', date.today()),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'create_date desc' )
            else:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '<', date.today())], order = 'create_date desc' )
        elif rec_obj.expiry_ageing=='expired_30':
            if rec_obj.product_id:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()),('expiration_date', '<=', date.today()+timedelta(days=30)),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'create_date desc' )
            else:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()),('expiration_date', '<=', date.today()+timedelta(days=30))], order = 'create_date desc' )
        elif rec_obj.expiry_ageing=='expired_60':
            if rec_obj.product_id: 
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()+timedelta(days=31)),('expiration_date', '<=', date.today()+timedelta(days=60)),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'create_date desc' )
            else:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()+timedelta(days=31)),('expiration_date', '<=', date.today()+timedelta(days=60))], order = 'create_date desc' )
        elif rec_obj.expiry_ageing=='expired_90':
            if rec_obj.product_id: 
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()+timedelta(days=61)),('expiration_date', '<=', date.today()+timedelta(days=90)),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'create_date desc' )
            else:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()+timedelta(days=61)),('expiration_date', '<=', date.today()+timedelta(days=90))], order = 'create_date desc' )
        elif rec_obj.expiry_ageing=='expired_91':
            if rec_obj.product_id: 
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()+timedelta(days=91)),('product_id','in', list(i.id for i in rec_obj.product_id))], order = 'create_date desc' )
            else:
                lot_data_obj = self.env['stock.lot'].search([('create_date', '<=', rec_obj.date), ('expiration_date', '>=', date.today()+timedelta(days=91))], order = 'create_date desc' )

        row_num = 6
        s_no = 1            
        total_qty =0
        
        for lot_data in sorted(lot_data_obj, key=lambda x: (x.product_id.product_tmpl_id.name, x.expiration_date)):
            
            if rec_obj.expiry_ageing != 'expired':           
            
                expiration_date = datetime.strptime(lot_data.expiration_date.strftime("%Y-%m-%d"),"%Y-%m-%d")            
                exprie_flag = 'Yes' if expiration_date.date() < date.today() else 'No'            
                exprie_flag_30 = 'Yes' if expiration_date.date() >= date.today() and expiration_date.date() <= date.today()+timedelta(days=30) else 'No'
                exprie_flag_60 = 'Yes' if expiration_date.date() >= date.today()+timedelta(days=31) and expiration_date.date() <= date.today()+timedelta(days=60) else 'No'
                exprie_flag_90 = 'Yes' if expiration_date.date() >= date.today()+timedelta(days=61) and expiration_date.date() <= date.today()+timedelta(days=90) else 'No'
                exprie_flag_91 = 'Yes' if expiration_date.date() >= date.today()+timedelta(days=91) else 'No'
            else:
                expiration_date = datetime.strptime(lot_data.expiration_date.strftime("%Y-%m-%d"),"%Y-%m-%d")            
                exprie_flag = 'Yes' if expiration_date.date() < date.today() else 'No' 
                exprie_flag_30 = exprie_flag_60 = exprie_flag_90 = exprie_flag_91 = '-'           

            
            sheet.write(row_num, 0, s_no, format12_a)
            sheet.write(row_num, 1, lot_data.name, format12)
            sheet.write(row_num, 2, lot_data.product_id.product_tmpl_id.name, format12)
            sheet.write(row_num, 3, "{:.2f}".format(lot_data.product_qty), format12_b)
            sheet.write(row_num, 4, "{:.2f}".format(lot_data.cost_price), format12_b)
            sheet.write(row_num, 5, ((lot_data.create_date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y %H:%M:%S")), format12)
            sheet.write(row_num, 6, ((lot_data.expiration_date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")), format12)
            sheet.write(row_num, 7, exprie_flag, format12)
            sheet.write(row_num, 8, exprie_flag_30, format12)
            sheet.write(row_num, 9, exprie_flag_60, format12)
            sheet.write(row_num, 10, exprie_flag_90, format12)
            sheet.write(row_num, 11, exprie_flag_91, format12)
            row_num += 1
            total_qty += lot_data.product_qty
            s_no += 1
        sheet.merge_range(row_num+2, 0, row_num+2, 2,"Grand Total", format11_a)
        sheet.write(row_num+2, 3, "{:.2f}".format(total_qty), format11_b)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()     
    
