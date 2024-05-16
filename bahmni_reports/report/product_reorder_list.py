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

class ProductReorderList(models.Model):   
    _name = 'product.reorder.list'
    _order = 'date desc'
    
    name = fields.Char(string="Report Name" , default='Product Reorder List')
    date = fields.Date('As On Date',required=True,default=lambda * a: time.strftime('%Y-%m-%d'))
    status = fields.Selection([('all','All'),('available','Stock Available'),('reorder','Order To Be Placed'),('nil','No Min Stock & Reorder Rule')],'Status',default="all")
    product_id = fields.Many2many('product.product','pro_reorder_reports','reports_id','product_id','Drugs Name',domain=[('active', '=', True),('type','=','product')])
    vendor_id = fields.Many2many('res.partner','vendor_reorder_reports','reports_id','vendor_id','Vendor Name',domain=[('active', '=', True),('supplier_rank', '>', 0)])
    
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
                'data': {'model': 'product.reorder.list',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Product_Reorder_List',
                         },
                'report_type': 'stock_xlsx',
            }
    
    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""        
        
        rec_obj = self.env['product.reorder.list'].search([('id', '=', data['self_rec'])])
        current_datetime = datetime.now() + timedelta(hours=5, minutes=30)
        rec_obj.write({ 'generate_date': time.strftime('%Y-%m-%d %H:%M:%S'),'generate_user_id':self.env.user.id	})
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        
        # Formats
        format1 = workbook.add_format({'font_size': 14, 'align': 'center', 'bold': True, 'border': 1})
        format2 = workbook.add_format({'font_size': 11, 'bold': True, 'border': 1, 'bg_color': '#a5f9f7'})   
        format2.set_align('center')        
        format11 = workbook.add_format({'font_size': 11, 'bold': True, 'border': 1, 'font_name': 'Calibri',})
        format11_a = workbook.add_format({'font_size': 11,'align': 'center', 'bold': True, 'border': 1, 'font_name': 'Calibri',})
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
        
        sheet.merge_range(0, 0, 0, 11,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
        sheet.merge_range(1, 0, 1, 11,'Product Reorder List', format1)
        sheet.merge_range(2, 0, 2, 5,"As On Date : "+ str(rec_obj.date.strftime("%d/%m/%Y")), format11)
        sheet.merge_range(3, 0, 3, 5,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)       
        sheet.merge_range(2, 6, 2, 11,"Drugs : "+product_names, format11)
        sheet.merge_range(3, 6, 3, 11,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11)         
 
        sheet.write(5, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        sheet.write(5, 1, "Product Name", format2)
        sheet.set_column('B:B', 32)
        sheet.write(5, 2, "Stock Qty", format2)
        sheet.set_column('C:C', 12)
        sheet.write(5, 3, "Sale Price", format2)
        sheet.set_column('D:D', 10)
        sheet.write(5, 4, "Minimum Qty", format2)
        sheet.set_column('E:E', 13)
        sheet.write(5, 5, "Reorder Qty", format2)
        sheet.set_column('F:F', 15)
        sheet.write(5, 6, "Vendor Name", format2)
        sheet.set_column('G:G', 25)
        sheet.write(5, 7, "Status", format2)
        sheet.set_column('H:H', 38)        
   
        if rec_obj.product_id and rec_obj.vendor_id:			
             product_obj = self.env['product.product'].search([('type', '=', 'product'),('id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids),
			('seller_ids.partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
        elif rec_obj.vendor_id:
             product_obj = self.env['product.product'].search([('type', '=', 'product'),
			('seller_ids.partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
        elif rec_obj.product_id:			
             product_obj = self.env['product.product'].search([('type', '=', 'product'),('id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids)])	
        else:
             product_obj = self.env['product.product'].search([('type', '=', 'product')])

        row_num = 6
        s_no = 1            
        total_qty =0       
        
        for product_data in sorted(product_obj, key=lambda x: x.name,reverse=False):            
            if rec_obj.status == 'all':
                if rec_obj.vendor_id:                
                    reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id),
                    ('vendor_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
                else:
                    reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id)])                
                if reorder_data:
                    qty_on_hand = reorder_data.qty_on_hand
                    lst_price = reorder_data.product_id.lst_price
                    product_min_qty = reorder_data.product_min_qty
                    qty_to_order = reorder_data.qty_to_order
                    supplier_name = reorder_data.supplier_id.partner_id.name if reorder_data.supplier_id else '-'
                    if reorder_data.qty_on_hand >= reorder_data.product_min_qty:
                        status = 'Stock Available'                    
                    elif reorder_data.qty_on_hand < reorder_data.product_min_qty:
                        status = 'Order To Be Placed'
                else:
                    qty_on_hand = 0
                    lst_price = 0
                    product_min_qty = 0
                    qty_to_order = 0
                    supplier_data = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_data.product_tmpl_id.id),
					('partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
                    supplier_name = ', '.join([supplierinfo.partner_id.name for supplierinfo in supplier_data]) if supplier_data else '-'
                    status = 'No Min Stock & Reorder Rule'
                
                sheet.write(row_num, 0, s_no, format12_a)
                sheet.write(row_num, 1, product_data.name, format12)
                sheet.write(row_num, 2, "{:.2f}".format(qty_on_hand), format12_b)
                sheet.write(row_num, 3, "{:.2f}".format(lst_price), format12_b)
                sheet.write(row_num, 4, "{:.2f}".format(product_min_qty), format12_b)
                sheet.write(row_num, 5, "{:.2f}".format(qty_to_order), format12_b)
                sheet.write(row_num, 6, supplier_name , format12)
                sheet.write(row_num, 7, status, format12)                
            
                row_num += 1
                if reorder_data:
                    total_qty += reorder_data.qty_on_hand
                s_no += 1
            
            elif rec_obj.status == 'available':
                if rec_obj.vendor_id:                
                    reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id),
                    ('vendor_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
                else:
                    reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id)]) 
                if reorder_data:
                    if reorder_data.qty_on_hand > reorder_data.product_min_qty:
                        status = 'Stock Available'                        
                        sheet.write(row_num, 0, s_no, format12_a)
                        sheet.write(row_num, 1, reorder_data.product_id.product_tmpl_id.name, format12)
                        sheet.write(row_num, 2, "{:.2f}".format(reorder_data.qty_on_hand), format12_b)
                        sheet.write(row_num, 3, "{:.2f}".format(reorder_data.product_id.lst_price), format12_b)
                        sheet.write(row_num, 4, "{:.2f}".format(reorder_data.product_min_qty), format12_b)
                        sheet.write(row_num, 5, "{:.2f}".format(reorder_data.qty_to_order), format12_b)
                        sheet.write(row_num, 6, reorder_data.supplier_id.partner_id.name if reorder_data.supplier_id else '-' , format12)
                        sheet.write(row_num, 7, status, format12)                
                        
                        row_num += 1
                        total_qty += reorder_data.qty_on_hand
                        s_no += 1
                    else:
                        pass
                else:
                    pass
            elif rec_obj.status == 'nil':
                
                reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id),
                ('vendor_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
                if not reorder_data:                    
                    qty_on_hand = 0
                    lst_price = 0
                    product_min_qty = 0
                    qty_to_order = 0
                    supplier_data = self.env['product.supplierinfo'].search([('product_tmpl_id', '=', product_data.product_tmpl_id.id),
					('partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
                    supplier_name = ', '.join([supplierinfo.partner_id.name for supplierinfo in supplier_data]) if supplier_data else '-'
                    status = 'No Min Stock & Reorder Rule'
                    
                    sheet.write(row_num, 0, s_no, format12_a)
                    sheet.write(row_num, 1, product_data.name, format12)
                    sheet.write(row_num, 2, "{:.2f}".format(qty_on_hand), format12_b)
                    sheet.write(row_num, 3, "{:.2f}".format(lst_price), format12_b)
                    sheet.write(row_num, 4, "{:.2f}".format(product_min_qty), format12_b)
                    sheet.write(row_num, 5, "{:.2f}".format(qty_to_order), format12_b)
                    sheet.write(row_num, 6, supplier_name , format12)
                    sheet.write(row_num, 7, status, format12)                 
                    
                    row_num += 1
                    total_qty += reorder_data.qty_on_hand
                    s_no += 1
                else:
                    pass
            elif rec_obj.status == 'reorder':
                if rec_obj.vendor_id:                
                    reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id),
                    ('vendor_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)])
                else:
                    reorder_data = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', product_data.id)]) 
                if reorder_data: 
                    if reorder_data.qty_on_hand < reorder_data.product_min_qty:
                        status = 'Order To Be Placed'
                        
                        sheet.write(row_num, 0, s_no, format12_a)
                        sheet.write(row_num, 1, reorder_data.product_id.product_tmpl_id.name, format12)
                        sheet.write(row_num, 2, "{:.2f}".format(reorder_data.qty_on_hand), format12_b)
                        sheet.write(row_num, 3, "{:.2f}".format(reorder_data.product_id.lst_price), format12_b)
                        sheet.write(row_num, 4, "{:.2f}".format(reorder_data.product_min_qty), format12_b)
                        sheet.write(row_num, 5, "{:.2f}".format(reorder_data.qty_to_order), format12_b)
                        sheet.write(row_num, 6, reorder_data.supplier_id.partner_id.name if reorder_data.supplier_id else '-' , format12)
                        sheet.write(row_num, 7, status, format12)                
                        
                        row_num += 1
                        total_qty += reorder_data.qty_on_hand
                        s_no += 1
                        
                    else:
                        pass
                else:
                    pass    
                    
            
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()     
    
