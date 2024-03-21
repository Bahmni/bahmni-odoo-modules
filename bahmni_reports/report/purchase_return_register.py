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

class PurchaseReturnRegister(models.Model):   
    _name = 'purchase.return.register'

    name = fields.Char(string="Report Name" , default='Purchase Return Register')
    from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    product_id = fields.Many2many('product.product','purchase_return_product_reports','reports_id','product_id','Drugs Name',domain=[('active', '=', True)])
    vendor_id = fields.Many2many('res.partner','purchase_return_vendor_reports','reports_id','vendor_id','Vendor Name',domain=[('active', '=', True),('supplier_rank', '>', 0)])
    
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
                'data': {'model': 'purchase.return.register',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Purchase_Return_Register',
                         },
                'report_type': 'stock_xlsx',
            }
    
    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""        
        
        rec_obj = self.env['purchase.return.register'].search([('id', '=', data['self_rec'])])
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
        format12 = workbook.add_format({'font_size': 10, 'font_name': 'Calibri', 'border': 1, })
        format12_a = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter','font_name': 'Calibri', 'border': 1})
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
        
        
        sheet.merge_range(0, 0, 0, 13,(rec_obj.env.user.company_id.name +", "+ rec_obj.env.user.company_id.street +", "+ rec_obj.env.user.company_id.state_id.name +"."), format1)
        sheet.merge_range(1, 0, 1, 13,'Purchase Return Register', format1)
        sheet.merge_range(2, 0, 2, 5,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
        sheet.merge_range(2, 6, 2, 13,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)
        
        sheet.merge_range(3, 0, 3, 5,"Vendor Name : "+ vendor_names, format11)
        sheet.merge_range(3, 6, 3, 13,"Drugs : "+ product_names, format11)
        
        sheet.merge_range(4, 0, 4, 5,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)       
        
        sheet.merge_range(4, 6, 4, 13,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 
        
       
 
        sheet.write(6, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        sheet.write(6, 1, "PO No / Date", format2)
        sheet.set_column('B:B', 20)
        sheet.write(6, 2, "Vendor Name", format2)
        sheet.set_column('C:C', 25)
        sheet.write(6, 3, "Product Name", format2)
        sheet.set_column('D:D', 18)
        sheet.write(6, 4, "Product Category", format2)
        sheet.set_column('E:E', 15)
        sheet.write(6, 5, "UOM", format2)
        sheet.set_column('F:F', 8)
        sheet.write(6, 6, "Purchase QTY", format2)
        sheet.set_column('G:G', 15)
        sheet.write(6, 7, "Unit Price", format2)
        sheet.set_column('H:H', 16)        
        sheet.write(6, 8, "Total Value", format2)
        sheet.set_column('I:I', 19)
        sheet.write(6, 9, "Serial Number", format2)
        sheet.set_column('J:J', 16)
        sheet.write(6, 10, "Return Date", format2)
        sheet.set_column('K:K', 16)
        sheet.write(6, 11, "Return QTY", format2)
        sheet.set_column('L:L', 16)
        sheet.write(6, 12, "Credit Amount", format2)
        sheet.set_column('M:M', 16)
        sheet.write(6, 13, "Status", format2)
        sheet.set_column('N:N', 16)
        
        
        po_data_obj = self.env['purchase.order'].search([
            ('date_approve', '>=', rec_obj.from_date),
            ('date_approve', '<=', rec_obj.to_date),
            ('state', '!=', 'draft'),
            ('order_line.product_id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids),
            ('partner_id', 'in', [i.id for i in rec_obj.vendor_id] if rec_obj.vendor_id else self.env['res.partner'].search([('active', '=', True),('supplier_rank', '>', 0)]).ids)
        ], order='name asc')
        
        
        row_num = 7
        s_no = 1            
        total_val =0
        total_credit = 0
        
        for data in po_data_obj:          
            
            purchase_line_obj = self.env['purchase.order.line'].search([
                ('order_id', '=', data.id)], order = 'create_date desc')           
            
            for order_line in sorted(purchase_line_obj, key=lambda x: x.product_id.product_tmpl_id.name,reverse=False):
                                
                return_move_obj = self.env['stock.move'].search([('purchase_line_id', '=', order_line.id) , ('to_refund','=','t')])
                refund_total_qty = 0
                lot_list = []
                if return_move_obj:
                    for return_move_line in return_move_obj.move_line_ids:
                        if return_move_line.lot_id:
                            lot_list.append(return_move_line.lot_id.name)
                        else:
                            lot_names = '-'
                        
                        refund_total_qty += return_move_line.qty_done
                        refund_date = ((return_move_line.date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y"))
                    lot_names = ', '.join(lot_list)
                    credit_amount  = (refund_total_qty * order_line.price_unit)
                    
                    sheet.write(row_num, 0, s_no, format12)
                    sheet.write(row_num, 1, data.name + " / " + (data.date_approve + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y"), format12)
                    sheet.write(row_num, 2, data.partner_id.name, format12)                        
                    sheet.write(row_num, 3, order_line.product_id.product_tmpl_id.name, format12)
                    sheet.write(row_num, 4, order_line.product_id.categ_id.name, format12)
                    sheet.write(row_num, 5, order_line.product_id.uom_id.name, format12)
                    sheet.write(row_num, 6, "{:.2f}".format(order_line.product_qty), format12_b)
                    sheet.write(row_num, 7, "{:.2f}".format(order_line.price_unit), format12_b)
                    sheet.write(row_num, 8, "{:.2f}".format(order_line.price_subtotal), format12_b)
                    sheet.write(row_num, 9, lot_names, format12)
                    sheet.write(row_num, 10, refund_date, format12)
                    sheet.write(row_num, 11, "{:.2f}".format(refund_total_qty), format12_b)
                    sheet.write(row_num, 12, "{:.2f}".format(credit_amount), format12_b)
                    sheet.write(row_num, 13, 'Done', format12)                
           
                    total_credit += credit_amount
                    total_val += order_line.price_subtotal
            
                    row_num +=1
                    s_no += 1
            
        
        sheet.merge_range(row_num+2, 0, row_num+2, 7,"Grand Total", format11_a)        
        sheet.write(row_num+2, 8, "{:.2f}".format(total_val), format11_b)
        sheet.merge_range(row_num+2, 9, row_num+2, 11, "", format11_b)
        sheet.write(row_num+2, 12, "{:.2f}".format(total_credit), format11_b)
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()     
    
