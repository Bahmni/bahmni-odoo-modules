import time
import pip
from datetime import datetime,date,timedelta


from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import io
import json
import datetime
from odoo.tools import date_utils

class PurchaseOrderRegister(models.Model):
    """ Generating Purchase Order Register """


    # Private attributes
    _name = 'purchase.register'
    _description = 'Purchase Order Register'

    # Fields declaration
    name = fields.Char(string="Report Name" , default='Purchase Order Register')
    tax_type = fields.Selection([('with_tax', 'With Tax'),('without_tax', 'Without Tax')],
                  string='Tax', required=True, widget='selection')
    from_date = fields.Date(string="From Date", required=True, default=fields.Date.today, index=True,
                 widget='date', help="Starting date for genarate report.")
    to_date = fields.Date(string="To Date", required=True,
                 default=fields.Date.today, index=True, help="End date for genarate report.")
    drug_ids = fields.Many2many(
        comodel_name='product.product',
        relation='purchase_register_drug_rel',
        column1='product_register_id',
        column2='drug_register_id',
        string="Drugs Name", index=True, domain=[('type', '=', 'product')])
    vendor_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='vendor_register_rel',
        column1='vedor_id',
        column2='vendor_register_id',
        string="Vendor Name", index=True,domain=[('active', '=', True),('supplier_rank', '>', 0)])

    #Entry info
    generate_date = fields.Datetime('Generate Date', store=True, readonly=True, default=time.strftime('%Y-%m-%d %H:%M:%S'))
    generate_user_id = fields.Many2one('res.users', 'Generate By',store=True, readonly=True, default=lambda self: self.env.user.id)

    def write(self,vals):
        vals.update({'generate_date': time.strftime('%Y-%m-%d %H:%M:%S'),'generate_user_id':self.env.user.id})
        return super(PurchaseOrderRegister, self).write(vals)

    @api.onchange('from_date', 'to_date')
    def onchange_date_validations(self):
        if self.from_date > fields.Date.today() or self.to_date > fields.Date.today():
           raise UserError(_("Future date is not allowed. Kindly choose correct from & to date."))


    def print_report(self):
        for rec in self:
            if rec.drug_ids:
               drug_list = rec.drug_ids
            else:
               drug_list = self.env['product.product'].search(['|',('active', '=', False),\
                                 ('active', '=', True),('type', '=', 'product')])
            current_datetime = datetime.datetime.now() + timedelta(hours=5, minutes=30)
            data = {
                'from_date': rec.from_date.strftime("%d/%m/%Y"),
                'to_date': rec.to_date.strftime("%d/%m/%Y"),
                'report_taken_by': self.env.user.partner_id.name,
                'taken_date': str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")),
                'drug_list': [drug.name for drug in rec.drug_ids],
                'vendor_list': [vendor.name for vendor in rec.vendor_ids],
                'company_name': rec.env.user.company_id.name,
                'company_street': rec.env.user.company_id.street,
                'company_state': rec.env.user.company_id.state_id.name,
                'drug_count': 'Limited' if rec.drug_ids else 'All',
                'tax_type': rec.tax_type,
                'po_details': [{
                              'po_no': po_details.name,
                              'date': po_details.date_order.strftime("%d/%m/%Y"),
                              'supplier_ref': po_details.partner_ref if po_details.partner_ref else '-',
                              'vendor_name': po_details.partner_id.name,
                              'product_details': [{
                                                  'product_name': po_line.name,
                                                  'product_category': po_line.product_id.product_tmpl_id.categ_id.name,
                                                  'uom': po_line.product_uom.name,
                                                  'qty': po_line.product_qty,
                                                  'unit_price': po_line.price_unit,
                                                  'tax': po_line.price_tax,
                                                  'total_value': po_line.price_total if rec.tax_type == 'with_tax' \
                                                                                     else po_line.price_subtotal
                                                 } for po_line in self.env['purchase.order.line'].search([('order_id', '=', po_details.id)])\
                                                 if po_line.product_id in rec.drug_ids or not rec.drug_ids]
                              } for po_details in self.env['purchase.order'].search([('date_order', '>=', rec.from_date),
                                                                                     ('date_order', '<=', rec.to_date),\
                                                                                     ('state', 'not in', ['draft', 'cancel'])],\
                                                                                     order='date_order asc')
                                                                 if po_details.partner_id in rec.vendor_ids or not rec.vendor_ids],
            }
            if not [po['product_details'] for po in data['po_details']]:
                raise UserError("No data available in given date range.")
            if not [po_line['product_name'] for po in data['po_details'] for po_line in po['product_details']]:
                raise UserError("No product data available in given date range.")

            return {
                'type': 'ir.actions.report',
                'data': {'model': 'purchase.register',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'purchase_order_register',
                         },
                'report_type': 'stock_xlsx',
            }

    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Formats
        format1 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'bold': True, 'border': 1})
        #format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 10, 'bold': True, 'border': 1, 'bg_color': '#a5f9f7'})

        format2.set_align('center')
        format11 = workbook.add_format({'font_size': 12, 'bold': True, 'border': 1,'font_name': 'Calibri',})
        head_value_format = workbook.add_format({'font_size': 12, 'font_name': 'Calibri','border': 1})
        basic_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        sno_format = workbook.add_format({'font_size': 10,'valign':'vcenter','font_name': 'Calibri','border': 1})
        sno_format.set_align('center')
        po_head_format = workbook.add_format({'font_size': 10, 'align':'left','valign':'vcenter',\
                   'font_name': 'Calibri','border': 1})
        po_line_format_str = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1})
        po_line_format_str.set_align('left')
        po_line_format_float = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1})
        po_line_format_float.set_align('right')
        grand_total_format = workbook.add_format({'font_size': 10, 'bold':True, 'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        grand_total_format.set_align('center')
        grand_total_format_ans = workbook.add_format({'font_size': 10, 'bold':True,\
                        'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        grand_total_format_ans.set_align('right')

        with_tax = 0
        if data['tax_type'] == 'with_tax':
            with_tax = 1
        sheet.merge_range(0, 0, 0, 10 + with_tax,
                          "%s, %s, %s"%(data['company_name'],data['company_street'],data['company_state']), format1)

        sheet.merge_range(1, 0, 1, 10 + with_tax,
                          'Purchase Order Register', format1)

        sheet.merge_range(2, 0, 2, 3,
                          "From Date %s: %s"%(' ' * 11,data['from_date']), format11)
        sheet.merge_range(3, 0, 3, 3,
                          "Vendor%s: %s"%(' ' * 17,'Limited' if data['vendor_list'] else 'All'), format11)
        sheet.merge_range(4, 0, 4, 3,
                          "Report Taken By   : %s" %(data['report_taken_by']), format11)

        sheet.merge_range(2, 7, 2, 10 + with_tax,
                          "To Date %s: %s"%(' ' * 18,data['to_date']), format11)
        sheet.merge_range(3, 7, 3, 10 + with_tax,
                          "Drugs %s: %s"%(' ' * 21, 'Limited' if data['drug_list'] else 'All'), format11)
        sheet.merge_range(4, 7, 4, 10 + with_tax,
                          "Taken Date & Time  : %s" %(data['taken_date']), format11)


        sheet.write(7, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        sheet.write(7, 1, "PO No", format2)
        sheet.set_column('B:B', 8)
        sheet.write(7,2, "Date", format2)
        sheet.set_column('C:C', 10)
        sheet.write(7,3, "Vendor Ref", format2)
        sheet.set_column('D:D', 14)
        sheet.write(7,4, "Vendor Name", format2)
        sheet.set_column('E:E', 14)
        sheet.write(7,5, "Product Name", format2)
        sheet.set_column('F:F', 14)
        sheet.write(7,6, "Product Category", format2)
        sheet.set_column('G:G', 18)
        sheet.write(7,7, "UOM", format2)
        sheet.set_column('H:H', 8)
        sheet.write(7,8, "Qty", format2)
        sheet.set_column('I:I', 6)
        sheet.write(7,9, "Unit Price", format2)
        sheet.set_column('J:J', 8)
        if data['tax_type'] == 'with_tax':
            sheet.write(7,10, "Tax", format2)
            sheet.set_column('K:K', 5)
            sheet.write(7,11, "Total Value", format2)
            sheet.set_column('L:L', 15)
        else:
            sheet.write(7,10, "Total Value", format2)
            sheet.set_column('K:K', 15)

        row_num = 8
        s_no = 1
        grand_total = 0
        line_count = 1
        po_line_len = 8
        total_tax = 0
        grand_total = 0
        head_row = 8
        for po in data['po_details']:
            if po['product_details']:
                po_line_len += (len(po['product_details']) - 1)
                if head_row == po_line_len:
                    sheet.write(head_row, 0, s_no, sno_format)
                    sheet.write(head_row, 1, po['po_no'], po_head_format)
                    sheet.write(head_row, 2, po['date'], po_head_format)
                    sheet.write(head_row, 3, po['supplier_ref'], po_head_format)
                    sheet.write(head_row, 4, po['vendor_name'], po_head_format)
                else:
                    sheet.merge_range(head_row, 0, po_line_len, 0, s_no, sno_format)
                    sheet.merge_range(head_row, 1, po_line_len, 1, po['po_no'], po_head_format)
                    sheet.merge_range(head_row, 2, po_line_len, 2, po['date'], po_head_format)
                    sheet.merge_range(head_row, 3, po_line_len, 3, po['supplier_ref'], po_head_format)
                    sheet.merge_range(head_row, 4, po_line_len, 4, po['vendor_name'], po_head_format)
                for po_line in po['product_details']:
                    sheet.write(row_num, 5, po_line['product_name'], po_line_format_str)
                    sheet.write(row_num, 6, po_line['product_category'], po_line_format_str)
                    sheet.write(row_num, 7, po_line['uom'], po_line_format_str)
                    sheet.write(row_num, 8, "{:.2f}".format(po_line['qty']), po_line_format_float)
                    sheet.write(row_num, 9, "{:.2f}".format(po_line['unit_price']), po_line_format_float)
                    if data['tax_type'] == 'with_tax':
                        sheet.write(row_num, 10, "{:.2f}".format(po_line['tax']), po_line_format_float)
                        sheet.write(row_num, 11, "{:.2f}".format(po_line['total_value']), po_line_format_float)
                        total_tax += po_line['tax']
                        grand_total += po_line['total_value']
                    else:
                        sheet.write(row_num, 10, "{:.2f}".format(po_line['total_value']), po_line_format_float)
                        grand_total += po_line['total_value']
                    row_num += 1
                    line_count += 1
                po_line_len += 1
                head_row = po_line_len
                s_no += 1


        if data['tax_type'] == 'with_tax':
            sheet.merge_range(2 + head_row, 8, 2 + head_row, 9,
                          "Grand Total", grand_total_format)
            sheet.write(2 + head_row,10,"{:.2f}".format(total_tax), grand_total_format_ans)
            sheet.write(2 + head_row,11,"{:.2f}".format(grand_total), grand_total_format_ans)
        else:
            sheet.merge_range(2 + head_row, 8, 2 + head_row, 9,
                          "Grand Total", grand_total_format)
            sheet.write(2 + head_row,10,"{:.2f}".format(grand_total), grand_total_format_ans)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def print_report_button(self):
        return self.print_report()
