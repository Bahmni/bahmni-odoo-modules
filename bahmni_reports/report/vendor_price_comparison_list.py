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

class VendorPriceComparisonList(models.Model):   
    _name = 'vendor.price.comparison.list'

    name = fields.Char(string="Report Name" , default='Vendor Price Comparison Register')
    from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    product_id = fields.Many2many('product.product','vendor_price_comparison_product_reports','reports_id','product_id','Product Name',domain=[('active', '=', True)])
    vendor_id = fields.Many2many('res.partner','vendor_price_comparison_vendor_reports','reports_id','vendor_id','Vendor Name',domain=[('active', '=', True),('supplier_rank', '>', 0)]) 
    
    generate_date = fields.Datetime('Generate Date', default=time.strftime('%Y-%m-%d %H:%M:%S'), readonly=True)
    generate_user_id = fields.Many2one('res.users', 'Generate By', default=lambda self: self.env.user.id, readonly=True)    
   
    
    def print_report(self):
        for rec in self:
            data = {                
                'self_rec': rec.id,
            }
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'vendor.price.comparison.list',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Vendor_Price_Comparison_Register',
                         },
                'report_type': 'stock_xlsx',
            }
    
    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""        
        
        rec_obj = self.env['vendor.price.comparison.list'].search([('id', '=', data['self_rec'])])
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
            
            
        vendor_list = []        
        if len(rec_obj.vendor_id) == 0:
            vendor_names = 'All'
        elif len(rec_obj.vendor_id) <= 3:
            for vendor in rec_obj.vendor_id:
                vendor_list.append(vendor.name)
            vendor_names = ', '.join(vendor_list)
        else:
            vendor_names = 'Limited'
        
        
        sheet.merge_range(0, 0, 0, 9,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
        sheet.merge_range(1, 0, 1, 9,'Vendor Price Comparison Register', format1)
        sheet.merge_range(2, 0, 2, 5,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
        sheet.merge_range(2, 6, 2, 9,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)
        
        sheet.merge_range(3, 0, 3, 5,"Vendor Name : "+vendor_names, format11)
        sheet.merge_range(3, 6, 3, 9,"Product : " + product_names, format11)
        
        sheet.merge_range(4, 0, 4, 5,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)       
        
        sheet.merge_range(4, 6, 4, 9,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 
        
        sheet.merge_range(6, 0, 6, 3,"", format11)
        sheet.merge_range(6, 4, 6, 6,"Purchase Details", format2)
        sheet.merge_range(6, 7, 6, 9,"Last Purchase", format2)
 
        sheet.write(7, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        sheet.write(7, 1, "Product Name", format2)
        sheet.set_column('B:B', 25)
        sheet.write(7, 2, "Product Category", format2)
        sheet.set_column('C:C', 18)
        sheet.write(7, 3, "UOM", format2)
        sheet.set_column('D:D', 9)
        sheet.write(7, 4, "Vendor Name", format2)
        sheet.set_column('E:E', 20)
        sheet.write(7, 5, "Cost Price/Unit", format2)
        sheet.set_column('F:F', 16)
        sheet.write(7, 6, "Date", format2)
        sheet.set_column('G:G', 10)
        sheet.write(7, 7, "Vendor Name", format2)
        sheet.set_column('H:H', 20)        
        sheet.write(7, 8, "Cost Price/Unit", format2)
        sheet.set_column('I:I', 16)
        sheet.write(7, 9, "Date", format2)
        sheet.set_column('J:J', 10)
        
        
        po_order_data_obj = self.env['purchase.order.line'].search([
            ('date_planned', '>=', rec_obj.from_date),
            ('date_planned', '<=', rec_obj.to_date),
            ('state', '!=', 'draft'),
            ('product_id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids),
            ('partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)
        ], order='date_planned asc')
        
        row_num = 8
        s_no = 1            
        total_val =0
        
        for data in sorted(po_order_data_obj, key=lambda x: x.date_planned,reverse=False):
           
            pre_purchase_obj = self.env['purchase.order.line'].search([
                ('id', '!=', data.id),
                ('date_planned', '<=', data.date_planned),
                ('state', '!=', 'draft'),
                ('product_id', '=', data.product_id.id)
            ], order='date_planned desc', limit=1)
            
            if pre_purchase_obj:
                pre_unit_price = pre_purchase_obj.price_unit
                pre_vendor_name = pre_purchase_obj.partner_id.name
                pre_date_planned = ((pre_purchase_obj.date_planned + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")) 
            else:
                pre_unit_price= 0.00
                pre_date_planned = '-'
                pre_vendor_name = '-'
            
            sheet.write(row_num, 0, s_no, format12_a)
            sheet.write(row_num, 1, data.product_id.product_tmpl_id.name, format12)
            sheet.write(row_num, 2, data.product_id.categ_id.name, format12)
            sheet.write(row_num, 3, data.product_id.uom_id.name, format12)
            sheet.write(row_num, 4, data.partner_id.name, format12)
            sheet.write(row_num, 5, "{:.2f}".format(data.price_unit), format12_b)
            sheet.write(row_num, 6, ((data.date_planned + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")), format12)
            
            sheet.write(row_num, 7, pre_vendor_name, format12)
            sheet.write(row_num, 8, "{:.2f}".format(pre_unit_price), format12_b)
            sheet.write(row_num, 9, pre_date_planned, format12)
                          
            row_num += 1            
            s_no += 1
        
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()     
    
