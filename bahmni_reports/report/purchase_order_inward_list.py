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

class PurchaseOrderInwardList(models.Model):   
    _name = 'purchase.order.inward.list'

    name = fields.Char(string="Report Name" , default='Purchase Order Based Inward Batch List')
    from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    product_id = fields.Many2many('product.product','purchase_order_inward_list_product_reports','reports_id','product_id','Drugs Name',domain=[('active', '=', True)])
    vendor_id = fields.Many2many('res.partner','purchase_order_inward_list_vendor_reports','reports_id','vendor_id','Vendor Name',domain=[('active', '=', True),('supplier_rank', '>', 0)]) 
    
    generate_date = fields.Datetime('Generate Date', default=time.strftime('%Y-%m-%d %H:%M:%S'), readonly=True)
    generate_user_id = fields.Many2one('res.users', 'Generate By', default=lambda self: self.env.user.id, readonly=True)    
   
    
    def print_report(self):
        for rec in self:
            data = {                
                'self_rec': rec.id,
            }
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'purchase.order.inward.list',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Purchase_Order_Based_Inward_Batch_List',
                         },
                'report_type': 'stock_xlsx',
            }
    
    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""        
        
        rec_obj = self.env['purchase.order.inward.list'].search([('id', '=', data['self_rec'])])
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
        
        
        sheet.merge_range(0, 0, 0, 11,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
        sheet.merge_range(1, 0, 1, 11,'Purchase Order Based Inward Batch List', format1)
        sheet.merge_range(2, 0, 2, 5,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
        sheet.merge_range(2, 6, 2, 11,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)
        
        sheet.merge_range(3, 0, 3, 5,"Vendor Name : "+vendor_names, format11)
        sheet.merge_range(3, 6, 3, 11,"Drugs : " + product_names, format11)
        
        sheet.merge_range(4, 0, 4, 5,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)       
        
        sheet.merge_range(4, 6, 4, 11,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 
        
         
        sheet.write(6, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        sheet.write(6, 1, "Order Reference", format2)
        sheet.set_column('B:B', 20)        
        sheet.write(6, 2, "Vendor Name", format2)
        sheet.set_column('C:C', 25)
        sheet.write(6, 3, "Product Name", format2)
        sheet.set_column('D:D', 20)
        sheet.write(6, 4, "Product Category", format2)
        sheet.set_column('E:E', 18)
        sheet.write(6, 5, "UOM", format2)
        sheet.set_column('F:F', 12)
        sheet.write(6, 6, "Inward Batch S.No.", format2)
        sheet.set_column('G:G', 19)
        sheet.write(6, 7, "Inward Date", format2)
        sheet.set_column('H:H', 15)
        sheet.write(6, 8, "Serial Number", format2)
        sheet.set_column('I:I', 17)
        sheet.write(6, 9, "Inward Batch Qty", format2)
        sheet.set_column('J:J', 19)        
        sheet.write(6, 10, "Cost Price", format2)
        sheet.set_column('K:K', 16)       
        sheet.write(6, 11, "Total Value", format2)
        sheet.set_column('L:L', 19)
        
                
        po_order_data_obj = self.env['purchase.order.line'].search([
            ('date_planned', '>=', rec_obj.from_date),
            ('date_planned', '<=', rec_obj.to_date),
            ('state', '!=', 'draft'),
            ('product_id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids),
            ('partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)
        ], order='date_planned asc')
        
        
        row_num = 7
        head_row = 7
        stok_move_len = 7
        s_no = 1            
        total_val =0
        
        for data in sorted(po_order_data_obj, key=lambda x: x.date_planned,reverse=False):     
            stock_obj = self.env['stock.move'].search([('purchase_line_id', '=', data.id)])          
            if stock_obj:
                for stock in stock_obj:        
                    stock_move_obj = self.env['stock.move.line'].search([('move_id', '=', stock.id),('lot_name','!=',False)])
                    if stock_move_obj:
                        stok_move_len += len(stock_move_obj) -1
                        if head_row == stok_move_len:
                            sheet.write(row_num, 0, s_no, format12_a)
                            sheet.write(row_num, 1, data.order_id.name + " / " + (data.date_planned + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y"), format12)                        
                            sheet.write(row_num, 2, data.order_id.partner_id.name, format12)
                            sheet.write(row_num, 3, data.product_id.product_tmpl_id.name, format12)
                            sheet.write(row_num, 4, data.product_id.categ_id.name, format12)
                            sheet.write(row_num, 5, data.product_id.uom_id.name, format12)              
                        else:
                            sheet.merge_range(head_row, 0, stok_move_len, 0, s_no, format12_a)
                            sheet.merge_range(head_row, 1, stok_move_len, 1, data.order_id.name + " / " + (data.date_planned + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y"), format12)
                            sheet.merge_range(head_row, 2, stok_move_len, 2, data.order_id.partner_id.name, format12)
                            sheet.merge_range(head_row, 3, stok_move_len, 3, data.product_id.product_tmpl_id.name, format12)
                            sheet.merge_range(head_row, 4, stok_move_len, 4, data.product_id.categ_id.name, format12)
                            sheet.merge_range(head_row, 5, stok_move_len, 5, data.product_id.uom_id.name, format12)
                        
                        line_count = 1    
                        for stock_move_line in stock_move_obj:
                            if stock_move_line.lot_name:
                                sheet.write(row_num, 6, line_count, format12_a)
                                sheet.write(row_num, 7, ((stock_move_line.date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")), format12)
                                sheet.write(row_num, 8, stock_move_line.lot_name, format12)
                                sheet.write(row_num, 9, "{:.2f}".format(stock_move_line.qty_done), format12_b)
                                sheet.write(row_num, 10, "{:.2f}".format(stock_move_line.cost_price), format12_b)                            
                                sheet.write(row_num, 11, "{:.2f}".format(stock_move_line.qty_done * stock_move_line.cost_price), format12_b)
                            else:
                                pass
                            
                            row_num += 1
                            line_count += 1
                            total_val += (stock_move_line.qty_done * stock_move_line.cost_price)
                        
                        stok_move_len +=1           
                        head_row = stok_move_len            
                        s_no += 1
                    
                    else:
                        pass
                
            else:
                pass
        
        sheet.merge_range(row_num+2, 0, row_num+2, 10,"Grand Total", format11_a)        
        sheet.write(row_num+2, 11, "{:.2f}".format(total_val), format11_b)    
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()     
    
