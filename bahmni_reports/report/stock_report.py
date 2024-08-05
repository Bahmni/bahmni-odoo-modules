import time
import pip
try:  
    import pandas as pd
except ImportError:
    pip.main(['install', 'pandas'])
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

class StockReport(models.Model):
    """ Generating Opening Stock and Closing Stock Reports """


    # Private attributes
    _name = 'stock.report'
    _description = 'Bahmni Reports'


    # Fields declaration
    name = fields.Char(string="Report Name" , default='Stock Statement')
    location_id = fields.Many2one('stock.location', string='Location Name', ondelete='restrict',
                  required=True, index=True, domain=[('usage', '=', 'internal')],
                  help='Select a target location from the list to generate report.')
    report_type = fields.Selection([('summary', 'Summary'),('details', 'Details')], 
                  string='Report Type', required=True, widget='selection',
                  help="Summary: Select multiple drugs simultaneously by using this option,\n"
                                 "Display essential details associated with the chosen drugs.\n"
                        "Details: Select the specific drug you want to work with,\n"
                                 "Display detailed overview of all transactions related to the chosen particular drug.\n")
    from_date = fields.Date(string="From Date", required=True, default=fields.Date.today, index=True,
                 widget='date', help="Starting date for genarate report.")
    to_date = fields.Date(string="To Date", required=True,
                 default=fields.Date.today, index=True, help="End date for genarate report.")
    output_type = fields.Selection([('excel', 'Excel'),('pdf', 'PDF')], 
                  nolabel=True, required=True, widget='selection')
    drug_ids = fields.Many2many(
        comodel_name='product.product',
        relation='product_drug_rel',
        column1='product_id',
        column2='drug_id',
        string="Drugs Name", index=True, domain=[('type', '=', 'product')])


    
    #Entry info
    generate_date = fields.Datetime('Generate Date', store=True, readonly=True, default=time.strftime('%Y-%m-%d %H:%M:%S'))
    generate_user_id = fields.Many2one('res.users', 'Generate By',store=True, readonly=True, default=lambda self: self.env.user.id)


    
    def write(self,vals):
        vals.update({'generate_date': time.strftime('%Y-%m-%d %H:%M:%S'),'generate_user_id':self.env.user.id})
        return super(StockReport, self).write(vals)

    @api.onchange('from_date', 'to_date')
    def onchange_date_validations(self):
        if self.from_date > fields.Date.today() or self.to_date > fields.Date.today():
           raise UserError(_("Future date is not allowed. Kindly choose correct from & to date."))
		

    def print_report(self):
        for rec in self:
            if len(self.drug_ids) > 1 and self.report_type == 'details':
                raise UserError(_("Unable to choose more than one drug if report type is detail. Kindly choose one drug to proceed further."))
            if len(self.drug_ids) == 0 and self.report_type == 'details':
                raise UserError(_("Kindly choose one drug to proceed further."))
            if rec.drug_ids:
               drug_list = rec.drug_ids
            else:
               drug_list = self.env['product.product'].search(['|',('active', '=', False),\
                                 ('active', '=', True),('type', '=', 'product')])
            current_datetime = datetime.datetime.now() + timedelta(hours=5, minutes=30)
            ## Opening Stock = Inward Stock - (Outward Stock + Internal Moved Stock)
            stock_move_line = self.env['stock.move.line']
            data = {
                'from_date': rec.from_date.strftime("%d/%m/%Y"),
                'to_date': rec.to_date.strftime("%d/%m/%Y"),
                'report_type': rec.report_type,
                'report_taken_by': self.env.user.partner_id.name,
                'taken_date': str(current_datetime.strftime("%d/%m/%Y %H:%M:%S")),
                'location_name': rec.location_id.complete_name,
                'drug_list': [drug.name for drug in rec.drug_ids],
                'company_name': rec.env.user.company_id.name,
                'company_street': rec.env.user.company_id.street,
                'company_state': rec.env.user.company_id.state_id.name,
                'drug_count': 'Limited' if rec.drug_ids else 'All',
                'drug': [{'name': drug.name,
                          'uom': drug.product_tmpl_id.uom_id.name,
                          ### Opening stock = (purchase order + Internal Inward) - (Issue + Internal Outward)
                          'open_stock_qty': (sum([po.qty_done for po in stock_move_line.search([('product_id', '=', drug.id),\
                               ('date', '<',  rec.from_date),('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'IN'), ##Purchase Order
                               ('move_id.state','=','done')])]) + sum([int_in.qty_done for int_in in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'), ##Internal Inward
                               ('move_id.state','=','done')])])) - (sum([int_out.qty_done for int_out in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'), ##Internal Outward
                               ('move_id.state','=','done')])]) + sum([issue.qty_done for issue in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_id', '=', rec.location_id.id),('move_id.state','=','done'),
                               ('picking_id.picking_type_id.sequence_code','=', 'OUT')])])), ##Item Issue
                          ##If Lot True means move line qty_done * Lot cost_price else
                          #latest purchase order unit price * move line qty_done is the total value. 
                          'open_stock_total': (sum([po.qty_done * (po.lot_id.cost_price if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for po in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'IN'),
                               ('move_id.state','=','done')])]) + sum([int_in.qty_done * (int_in.lot_id.cost_price \
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for int_in in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'),
                               ('move_id.state','=','done')])])) - (sum([int_out.qty_done * (int_out.cost_price\
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for int_out in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'),
                               ('move_id.state','=','done')])]) + sum([issue.qty_done * (issue.cost_price\
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for issue in stock_move_line.search([\
                               ('product_id', '=', drug.id),('date', '<',  rec.from_date),
                               ('picking_id.location_id', '=', rec.location_id.id),('move_id.state','=','done'),
                               ('picking_id.picking_type_id.sequence_code','=', 'OUT')])])),
                          ## Purchase Stock
                          'purchase_qty': sum([po.qty_done for po in stock_move_line.search([('product_id', '=', drug.id),\
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'IN'), ##Purchase Order
                               ('move_id.state','=','done')])]),
                          'purchase_total': sum([po.qty_done * (po.lot_id.cost_price\
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for po in stock_move_line.search([('product_id', '=', drug.id),\
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'IN'),
                               ('move_id.state','=','done')])]),
                          ## Internal Inward Stock
                          'internal_inward_qty': sum([int_in.qty_done for int_in in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('location_id.name','!=', 'Inventory adjustment'),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'),('move_id.state','=','done')])]), ##Internal Inward
                          'internal_inward_total': sum([int_in.qty_done * (int_in.lot_id.cost_price \
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for int_in in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('location_id.name','!=', 'Inventory adjustment'),
                               ('picking_id.location_dest_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'),('move_id.state','=','done')])]),
                          ##Inventory Adjustment Stock
                          'inventory_adj_qty': sum([int_in.qty_done for int_in in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('location_dest_id', '=', rec.location_id.id),
                               ('location_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])]) - 
                               sum([int_out.qty_done for int_out in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('location_id', '=', rec.location_id.id),
                               ('location_dest_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])]),
                          'inventory_adj_total': sum([adj_in.qty_done * (adj_in.lot_id.cost_price \
                                if drug.tracking == "lot" else \
                                sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([ \
                                ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)]))
                                for adj_in in stock_move_line.search([('product_id', '=', drug.id),
                                ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                                ('location_dest_id', '=', rec.location_id.id),
                                ('location_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])]) -
                                sum([adj_out.qty_done * (adj_out.lot_id.cost_price \
                                if drug.tracking == "lot" else \
                                sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([ \
                                ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)]))
                                for adj_out in stock_move_line.search([('product_id', '=', drug.id),
                                ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                                ('location_id', '=', rec.location_id.id),
                                ('location_dest_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])]),
                          ## Internal Outward Stock
                          'internal_outward_qty': sum([int_out.qty_done for int_out in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('location_dest_id.name','!=', 'Inventory adjustment'),
                               ('picking_id.location_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'),('move_id.state','=','done')])]), ##Internal outward
                          'internal_outward_total': sum([int_out.qty_done * (int_out.lot_id.cost_price \
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for int_out in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('picking_id.location_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'INT'),('move_id.state','=','done')])]),
                          ## Item Issue
                          'issue_qty': sum([issue.qty_done for issue in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('picking_id.location_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'OUT'),('move_id.state','=','done')])]), ##Item Issue
                          'issue_total': sum([issue.qty_done * (issue.lot_id.cost_price \
                               if drug.tracking == "lot" else\
                               sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                               ('product_id', '=', drug.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                               for issue in stock_move_line.search([('product_id', '=', drug.id),
                               ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                               ('picking_id.location_id', '=', rec.location_id.id),
                               ('picking_id.picking_type_id.sequence_code','=', 'OUT'),('move_id.state','=','done')])])}\
                           for drug in drug_list]\
                           if rec.report_type == 'summary'\
                           else [{'name': rec.drug_ids.name,
                                  'uom': rec.drug_ids.product_tmpl_id.uom_id.name,
				  'open_stock_qty': (sum([po.qty_done for po in stock_move_line.search([('product_id', '=', rec.drug_ids.id),\
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'IN'), ##Purchase Order
				       ('move_id.state','=','done')]) if po.date < days]) + sum([int_in.qty_done\
                                       for int_in in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'), ##Internal Inward
				       ('move_id.state','=','done')]) if int_in.date < days])) - (sum([int_out.qty_done\
                                       for int_out in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'), ##Internal Outward
				       ('move_id.state','=','done')]) if int_out.date < days]) + sum([issue.qty_done\
                                       for issue in stock_move_line.search([('product_id', '=', rec.drug_ids.id),\
				       ('picking_id.location_id', '=', rec.location_id.id),('move_id.state','=','done'),
				       ('picking_id.picking_type_id.sequence_code','=', 'OUT')]) if issue.date < days])), ##Issue
				  'open_stock_total': (sum([po.qty_done * ( po.lot_id.cost_price \
                                       if rec.drug_ids.tracking == "lot" else\
                                       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                                       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                                       for po in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'IN'),
				       ('move_id.state','=','done')]) if po.date < days]) + sum([int_in.qty_done * (int_in.lot_id.cost_price\
                                       if rec.drug_ids.tracking == "lot" else\
                                       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                                       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                                       for int_in in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'), ('move_id.state','=','done')])\
                                       if int_in.date < days])) - (sum([int_out.qty_done * (int_out.lot_id.cost_price\
                                       if rec.drug_ids.tracking == "lot" else\
                                       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                                       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                                       for int_out in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'), ('move_id.state','=','done')])\
                                       if int_out.date < days]) + sum([issue.qty_done * (issue.lot_id.cost_price
                                       if rec.drug_ids.tracking == "lot" else\
                                       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
                                       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
                                       for issue in stock_move_line.search([('product_id', '=', rec.drug_ids.id),\
				       ('picking_id.location_id', '=', rec.location_id.id),('move_id.state','=','done'),
				       ('picking_id.picking_type_id.sequence_code','=', 'OUT')]) if issue.date < days])),
				  'purchase_qty': sum([po.qty_done for po in stock_move_line.search([('product_id', '=', rec.drug_ids.id),\
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'IN'), ##Purchase Order
				       ('move_id.state','=','done')]) if po.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       po.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]),
				  'purchase_total': sum([po.qty_done * (po.lot_id.cost_price\
				       if rec.drug_ids.tracking == "lot" else\
				       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
				       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
				       for po in stock_move_line.search([('product_id', '=', rec.drug_ids.id),\
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'IN'),
				       ('move_id.state','=','done')]) if po.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       po.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]),
				  'internal_inward_qty': sum([int_in.qty_done for int_in in stock_move_line.search([\
                                       ('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
                                       ('location_id.name','!=', 'Inventory adjustment'),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'),
                                       ('move_id.state','=','done')]) if int_in.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       int_in.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]), ##Internal Inward
				  'internal_inward_total': sum([int_in.qty_done * (int_in.lot_id.cost_price \
				       if rec.drug_ids.tracking == "lot" else\
				       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
				       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
				       for int_in in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_dest_id', '=', rec.location_id.id),
                                       ('location_id.name','!=', 'Inventory adjustment'),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'),
                                       ('move_id.state','=','done')]) if int_in.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       int_in.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]),
				  'inventory_adj_qty': sum([int_in.qty_done for int_in in stock_move_line.search([\
                                       ('product_id', '=', rec.drug_ids.id),
				       ('location_dest_id', '=', rec.location_id.id),
				       ('location_id.name','=', 'Inventory adjustment'),
                                       ('move_id.state','=','done')]) if int_in.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       int_in.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]) - 
                                       sum([int_out.qty_done for int_out in stock_move_line.search([\
                                       ('product_id', '=', rec.drug_ids.id),
                                       ('location_id', '=', rec.location_id.id),
                                       ('location_dest_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])
                                       if int_out.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       int_out.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]), ##Inventory Adjustment
				  'inventory_adj_total': sum([adj_in.qty_done * (adj_in.lot_id.cost_price \
                                        if rec.drug_ids.tracking == "lot" else \
                                        sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([ \
                                        ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)]))
                                        for adj_in in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
                                        ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                                        ('location_dest_id', '=', rec.location_id.id),
                                        ('location_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])]) -
                                        sum(adj_out.qty_done * (adj_out.lot_id.cost_price \
                                        if rec.drug_ids.tracking == "lot" else \
                                        sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([ \
                                        ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)]))
                                        for adj_out in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
                                        ('date', '>=',  rec.from_date),('date', '<=',  rec.to_date),
                                        ('location_id', '=', rec.location_id.id),
                                        ('location_dest_id.name','=', 'Inventory adjustment'),('move_id.state','=','done')])),
				  ## Internal Outward Stock
				  'internal_outward_qty': sum([int_out.qty_done for int_out in stock_move_line.search([\
                                       ('product_id', '=', rec.drug_ids.id),
                                       ('location_dest_id.name','!=', 'Inventory adjustment'),
				       ('picking_id.location_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'),('move_id.state','=','done')]) 
                                       if int_out.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       int_out.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]),
				  'internal_outward_total': sum([int_out.qty_done * (int_out.lot_id.cost_price \
				       if rec.drug_ids.tracking == "lot" else\
				       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
				       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
				       for int_out in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'INT'),('move_id.state','=','done')])\
                                       if int_out.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       int_out.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]),
				  ## Item Issue
				  'issue_qty': sum([issue.qty_done for issue in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'OUT'),('move_id.state','=','done')])\
                                       if issue.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       issue.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]), ##Item Issue
				  'issue_total': sum([issue.qty_done * (issue.lot_id.cost_price \
				       if rec.drug_ids.tracking == "lot" else\
				       sum([po.price_total / po.product_qty for po in self.env['purchase.order.line'].search([\
				       ('product_id', '=', rec.drug_ids.id), ('state', '=', 'purchase')], order='id desc',limit=1)])) 
				       for issue in stock_move_line.search([('product_id', '=', rec.drug_ids.id),
				       ('picking_id.location_id', '=', rec.location_id.id),
				       ('picking_id.picking_type_id.sequence_code','=', 'OUT'),('move_id.state','=','done')])\
                                       if issue.date.strftime('%d-%m-%Y') == days.strftime('%d-%m-%Y') and\
                                       issue.date.strftime('%H:%M:%S') > days.strftime('%H:%M:%S')]),
                                  'date': days.strftime('%d-%m-%Y')} \
                                  for days in pd.date_range(start=pd.to_datetime(rec.from_date), end=pd.to_datetime(rec.to_date))]}
            excel = {
                'type': 'ir.actions.report',
                'data': {'model': 'stock.report',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': 'Stock Statement - Summary' if rec.report_type == 'summary' else 'Stock Statement - Details',
                         },
                'report_type': 'stock_xlsx',
            }

            pdf = {'data': data}
            return pdf if rec.output_type == 'pdf' else excel

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
        opening_stock_format_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#ADD8E6'})
        opening_stock_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#ADD8E6'})
        opening_stock_format.set_align('right')
        purchase_format_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#98FB98'})
        purchase_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#98FB98'})
        purchase_format.set_align('right')
        issue_format_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#FFE4B5'})
        issue_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#FFE4B5'})
        issue_format.set_align('right')
        internal_inward_format_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#FFB6C1'})
        inventory_adj_format_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#cef542'})
        internal_inward_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#FFB6C1'})
        internal_inward_format.set_align('right')
        inventory_adj_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#cef542'})
        inventory_adj_format.set_align('right')
        internal_outward_format_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#F0FFFF'})
        internal_outward_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#F0FFFF'})
        internal_outward_format.set_align('right')
        closing_stock_head = workbook.add_format({'font_size': 10, 'bold':True,'align':'center','font_name': 'Calibri','border': 1, 'bg_color': '#FDDC5C'})
        closing_stock_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#FDDC5C'})
        closing_stock_format.set_align('right')
        basic_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        sno_format = workbook.add_format({'font_size': 10, 'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        sno_format.set_align('center')
        grand_total_format = workbook.add_format({'font_size': 10, 'bold':True, 'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        grand_total_format.set_align('center')
        grand_total_format_ans = workbook.add_format({'font_size': 10, 'bold':True, 'font_name': 'Calibri','border': 1, 'bg_color': '#DCDCDC'})
        grand_total_format_ans.set_align('right')
        if data['report_type'] == 'summary':
            sheet.merge_range(0, 0, 0, 13,
                          "%s, %s, %s"%(data['company_name'],data['company_street'],data['company_state']), format1)
            sheet.merge_range(1, 0, 1, 13,
                          'Stock Statement - Summary', format1)
        else:
            sheet.merge_range(0, 0, 0, 14,
                          "%s, %s, %s"%(data['company_name'],data['company_street'],data['company_state']), format1)
            sheet.merge_range(1, 0, 1, 14,
                          'Stock Statement - Details', format1)
        sheet.merge_range(2, 0, 2, 2,
                          "From Date %s: %s"%(' ' * 11,data['from_date']), format11)
        sheet.merge_range(3, 0, 3, 2,
                          "Location Name %s: %s"%(' ' * 4,data['location_name']), format11)
        sheet.merge_range(4, 0, 4, 2,
                          "Report Taken By  : %s" %(data['report_taken_by']), format11)
        if data['report_type'] == 'summary':
            sheet.merge_range(2, 8, 2, 13,
                          "To Date %s: %s"%(' ' * 18,data['to_date']), format11)
            sheet.merge_range(3, 8, 3, 13,
                          "Drugs %s: %s"%(' ' * 21, 'Limited' if data['drug_list'] else 'All'), format11)
            sheet.merge_range(4, 8, 4, 13,
                          "Taken Date & Time : %s" %(data['taken_date']), format11)
        else:
            sheet.merge_range(2, 8, 2, 14,
                          "To Date %s: %s"%(' ' * 18,data['to_date']), format11)
            sheet.merge_range(3, 8, 3, 14,
                          "Drugs %s: %s"%(' ' * 21,data['drug_list'][0]), format11)
            sheet.merge_range(4, 8, 4, 14,
                          "Taken Date & Time : %s" %(data['taken_date']), format11)
        details = 0 if data['report_type'] == 'summary' else 1
        sheet.merge_range(6, 3 + details, 6, 4 + details,
                          "Opening Stock", opening_stock_format_head)
        sheet.merge_range(6, 5 + details, 6, 6 + details,
                          "Purchase", purchase_format_head)
        sheet.merge_range(6, 7 + details, 6, 8 + details,
                          "Internal Inward", internal_inward_format_head)
        sheet.merge_range(6, 9 + details, 6, 10 + details,
                          "Inventory Adjustment", inventory_adj_format_head)
        sheet.merge_range(6, 11 + details, 6, 12 + details,
                          "Internal Outward", internal_outward_format_head)
        sheet.merge_range(6, 13 + details, 6, 14 + details,
                          "Issue", issue_format_head)
        sheet.merge_range(6, 15 + details, 6, 16 + details,
                          "Closing Stock", closing_stock_head)
        sheet.write(7, 0, "S.No", format2)
        sheet.set_column('A:A', 5)
        if data['report_type'] == 'details':
            sheet.write(7, 1, "Date", format2)
            sheet.set_column('B:B', 8)
        sheet.write(7, 2 if data['report_type'] == 'details' else 1, "Product Name", format2)
        sheet.set_column('C:C' if data['report_type'] == 'details' else'B:B', 20)
        sheet.write(7,3 if data['report_type'] == 'details' else 2, "UOM", format2)
        sheet.set_column('D:D' if data['report_type'] == 'details' else'C:C', 7)
        sheet.write(7,4 if data['report_type'] == 'details' else 3, "Qty", format2)
        sheet.set_column('E:E' if data['report_type'] == 'details' else 'D:D', 7)
        sheet.write(7,5 if data['report_type'] == 'details' else 4, "Total Value", format2)
        sheet.set_column('F:F' if data['report_type'] == 'details' else 'E:E', 12)
        sheet.write(7,6 if data['report_type'] == 'details' else 5, "Qty", format2)
        sheet.set_column('G:G' if data['report_type'] == 'details' else 'F:F', 7)
        sheet.write(7,7 if data['report_type'] == 'details' else 6, "Total Value", format2)
        sheet.set_column('H:H' if data['report_type'] == 'details' else 'G:G', 12)
        sheet.write(7,8 if data['report_type'] == 'details' else 7, "Qty", format2)
        sheet.set_column('I:I' if data['report_type'] == 'details' else 'H:H', 7)
        sheet.write(7,9 if data['report_type'] == 'details' else 8, "Total Value", format2)
        sheet.set_column('J:J' if data['report_type'] == 'details' else 'I:I', 12)
        sheet.write(7,10 if data['report_type'] == 'details' else 9, "Qty", format2)
        sheet.set_column('K:K' if data['report_type'] == 'details' else 'J:J', 7)
        sheet.write(7,11 if data['report_type'] == 'details' else 10, "Total Value", format2)
        sheet.set_column('L:L' if data['report_type'] == 'details' else 'K:K', 12)
        sheet.write(7,12 if data['report_type'] == 'details' else 11, "Qty", format2)
        sheet.set_column('M:M' if data['report_type'] == 'details' else 'L:L', 7)
        sheet.write(7,13 if data['report_type'] == 'details' else 12, "Total Value", format2)
        sheet.set_column('N:N' if data['report_type'] == 'details' else 'M:M', 12)
        sheet.write(7,14 if data['report_type'] == 'details' else 13, "Qty", format2)
        sheet.set_column('O:O' if data['report_type'] == 'details' else 'N:N', 7)
        sheet.write(7,15 if data['report_type'] == 'details' else 14, "Total Value", format2)
        sheet.set_column('P:P' if data['report_type'] == 'details' else 'O:O', 12)
        sheet.write(7,16 if data['report_type'] == 'details' else 15, "Qty", format2)
        sheet.set_column('Q:Q' if data['report_type'] == 'details' else 'P:P', 7)
        sheet.write(7,17 if data['report_type'] == 'details' else 16, "Total Value", format2)
        sheet.set_column('R:R' if data['report_type'] == 'details' else 'Q:Q', 12)
        row_num = 8
        s_no = 1
        grand_total = 0
        for drug in data['drug']:
            if drug['open_stock_qty'] or drug['purchase_qty'] or drug['issue_qty'] or drug['internal_inward_qty'] or drug['internal_outward_qty'] or drug['inventory_adj_qty']:
                sheet.write(row_num, 0, s_no, sno_format)
                if data['report_type'] == 'details':
                   sheet.write(row_num, 1, drug['date'], basic_format)
                else:
                   ...
                sheet.write(row_num,2 if data['report_type'] == 'details' else 1, drug['name'], basic_format)
                sheet.write(row_num,3 if data['report_type'] == 'details' else 2, drug['uom'], basic_format)
                sheet.write(row_num,4 if data['report_type'] == 'details' else 3, "{:.2f}".format(drug['open_stock_qty']), opening_stock_format)
                sheet.write(row_num,5 if data['report_type'] == 'details' else 4,"{:.2f}".format(drug['open_stock_total']), opening_stock_format)
                sheet.write(row_num,6 if data['report_type'] == 'details' else 5, "{:.2f}".format(drug['purchase_qty']), purchase_format)
                sheet.write(row_num,7 if data['report_type'] == 'details' else 6,"{:.2f}".format(drug['purchase_total']), purchase_format)
                sheet.write(row_num,8 if data['report_type'] == 'details' else 7,"{:.2f}".format(drug['internal_inward_qty']), internal_inward_format)
                sheet.write(row_num,9 if data['report_type'] == 'details' else 8, "{:.2f}".format(drug['internal_inward_total']), internal_inward_format)
                sheet.write(row_num,10 if data['report_type'] == 'details' else 9,"{:.2f}".format(drug['inventory_adj_qty']), inventory_adj_format)
                sheet.write(row_num,11 if data['report_type'] == 'details' else 10, "{:.2f}".format(drug['inventory_adj_total']), inventory_adj_format)
                sheet.write(row_num,12 if data['report_type'] == 'details' else 11,"{:.2f}".format(drug['internal_outward_qty']), internal_outward_format)
                sheet.write(row_num,13 if data['report_type'] == 'details' else 12,"{:.2f}".format(drug['internal_outward_total']), internal_outward_format)
                sheet.write(row_num,14 if data['report_type'] == 'details' else 13,"{:.2f}".format(drug['issue_qty']), issue_format)
                sheet.write(row_num,15 if data['report_type'] == 'details' else 14,"{:.2f}".format(drug['issue_total']), issue_format)
                closing_stock_qty = (drug['open_stock_qty'] + drug['purchase_qty'] + \
                                 drug['internal_inward_qty'] + drug['inventory_adj_qty']) -\
                               (drug['internal_outward_qty'] + drug['issue_qty'])
                closing_stock_total = (drug['open_stock_total'] + drug['purchase_total'] + \
                               drug['internal_inward_total'] + drug['inventory_adj_total']) -\
                               (drug['internal_outward_total'] + drug['issue_total'])
                grand_total += closing_stock_total
                sheet.write(row_num,16 if data['report_type'] == 'details' else 15,"{:.2f}".format(closing_stock_qty), closing_stock_format)
                sheet.write(row_num,17 if data['report_type'] == 'details' else 16,"{:.2f}".format(closing_stock_total), closing_stock_format)
                row_num += 1
                s_no += 1

        if data['report_type'] != 'details':
            sheet.merge_range(10 + s_no, 14 + details, 10 + s_no, 15 + details,
                          "Grand Total", grand_total_format)
            sheet.write(10+s_no,16,"{:.2f}".format(grand_total), grand_total_format_ans)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def print_report_button(self):
        if self.output_type == 'excel':
            return self.print_report()
        else:
            report_action = self.env.ref('bahmni_reports.bahmni_reports_stock')
            return report_action.report_action(self)
