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

class LocationWiseDrugMovement(models.Model):   
    _name = 'location.wise.drug.movement'

    name = fields.Char(string="Report Name" , default='Location Wise Product Movement Register')
    from_date = fields.Date('From Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    to_date = fields.Date('To Date',default=lambda * a: time.strftime('%Y-%m-%d'))
    product_id = fields.Many2many('product.product','location_wise_drug_movement_product_reports','reports_id','product_id','Product Name',domain=[('active', '=', True)])
    source_location_id = fields.Many2one('stock.location', 'From Location',domain=[('active', '=', True),('usage', 'in', ('internal','supplier','customer'))])  
    dest_location_id = fields.Many2one('stock.location', 'Destination Location',domain=[('active', '=', True),('usage', 'in', ('internal','supplier','customer'))])  
    
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
                'data': {'model': 'location.wise.drug.movement',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Location_Wise_Product_Movement_Register',
                         },
                'report_type': 'stock_xlsx',
            }
    
    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""        
        
        rec_obj = self.env['location.wise.drug.movement'].search([('id', '=', data['self_rec'])])
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
        sheet.merge_range(1, 0, 1, 8,'Location Wise Product Movement Register', format1)
        sheet.merge_range(2, 0, 2, 4,"From Date : "+ str(rec_obj.from_date.strftime("%d/%m/%Y")), format11)
        sheet.merge_range(2, 5, 2, 8,"To Date : "+ str(rec_obj.to_date.strftime("%d/%m/%Y")), format11)
        
        sheet.merge_range(3, 0, 3, 4,"From Location : "+ str(rec_obj.source_location_id.complete_name if rec_obj.source_location_id.complete_name else 'All'), format11)
        sheet.merge_range(3, 5, 3, 8,"Product : "+product_names, format11)
        
        sheet.merge_range(4, 0, 4, 8,"Destination Location : "+ str(rec_obj.dest_location_id.complete_name if rec_obj.dest_location_id.complete_name else 'All'), format11)
        
        sheet.merge_range(5, 0, 5, 4,"Report Taken By  : "+ str(self.env.user.partner_id.name), format11)          
        sheet.merge_range(5, 5, 5, 8,"Taken Date & Time : "+ str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")), format11) 
       
 
        sheet.write(7, 0, "S.No", format2)
        sheet.set_column('A:A', 5)        
        sheet.write(7, 1, "Product Name", format2)
        sheet.set_column('B:B', 25)        
        sheet.write(7, 2, "UOM", format2)
        sheet.set_column('C:C', 10)
        sheet.write(7, 3, "Qty", format2)
        sheet.set_column('D:D', 8)
        sheet.write(7, 4, "Serial No", format2)
        sheet.set_column('E:E', 16)
        sheet.write(7, 5, "Cost Price", format2)
        sheet.set_column('F:F', 12)
        sheet.write(7, 6, "Total Value", format2)
        sheet.set_column('G:G', 16)        
        sheet.write(7, 7, "From Location", format2)
        sheet.set_column('H:H', 19)
        sheet.write(7, 8, "To Location", format2)
        sheet.set_column('I:I', 21)
        sheet.write(7, 9, "Move Date", format2)
        sheet.set_column('J:J', 16)
        
        
        
        move_data_obj = self.env['stock.move.line'].search([
            ('date', '>=', rec_obj.from_date),
            ('date', '<=', rec_obj.to_date),
            ('state', '=', 'done'),
            ('product_id', 'in', [i.id for i in rec_obj.product_id] if rec_obj.product_id else self.env['product.product'].search([]).ids),
            ('location_id', 'in', rec_obj.source_location_id.ids if rec_obj.source_location_id else self.env['stock.location'].search([('active', '=', True),('usage', 'in', ('internal','supplier','customer'))]).ids),
            ('location_dest_id', '=', rec_obj.dest_location_id.ids if rec_obj.dest_location_id else self.env['stock.location'].search([('active', '=', True),('usage', 'in', ('internal','supplier','customer'))]).ids)
        ], order='product_id desc')
        
        
        row_num = 8
        s_no = 1            
        total_val =0
        
        for data in sorted(move_data_obj, key=lambda x: x.date,reverse=False):
           
            purchase_obj = self.env['purchase.order.line'].search([('product_id', '=', data.product_id.id)], order = 'create_date desc', limit=1)
            
            if data.lot_id:
                cost_price = data.lot_id.cost_price   
                lot_name = data.lot_id.name  
            else:
                cost_price = data.product_id.standard_price
                lot_name = '-'
            
            sheet.write(row_num, 0, s_no, format12_a)
            sheet.write(row_num, 1, data.product_id.product_tmpl_id.name, format12)
            sheet.write(row_num, 2, data.product_id.uom_id.name, format12)
            sheet.write(row_num, 3, "{:.2f}".format(data.qty_done), format12_b)
            sheet.write(row_num, 4, lot_name, format12)
            sheet.write(row_num, 5, "{:.2f}".format(cost_price), format12_b)
            sheet.write(row_num, 6, "{:.2f}".format((data.qty_done * cost_price)), format12_b)
            sheet.write(row_num, 7, data.location_id.complete_name, format12)
            sheet.write(row_num, 8, data.location_dest_id.complete_name, format12)
            sheet.write(row_num, 9, ((data.date + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y")), format12)
            row_num += 1
            total_val += (data.qty_done * cost_price)
            s_no += 1
                
       
           
        
        sheet.merge_range(row_num+2, 0, row_num+2, 5,"Grand Total", format11_a)
        sheet.write(row_num+2, 6, "{:.2f}".format(total_val), format11_b)
            
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()     
    
