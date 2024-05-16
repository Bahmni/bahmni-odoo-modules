
from datetime import datetime
from dateutil import tz

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    
    stock_picking_time = fields.Datetime(string="Stock Picking_time", store=True)
    @api.model
    def create(self,vals):
        if not vals.get('origin_returned_move_id'):
            if vals.get('origin'):
                sale_order = self.env['sale.order'].search([('name','=',str(vals.get('origin')))])
                if any(sale_order) and sale_order.location_id:
                    vals.update({'location_id':sale_order.location_id.id})
        return super(StockMove,self).create(vals)
