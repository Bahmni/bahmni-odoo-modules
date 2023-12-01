# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF

logger = logging.getLogger(__name__)

class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    available_qty = fields.Integer(string="Available Qty")
    picking_type = fields.Char(string="Operation Type")

    def save(self):
        '''This method is overridden to restrict user from assigning expired lots'''
        for pack in self:
            if pack.product_id.tracking != 'none':
                for lot in pack.pack_lot_ids:
                    if lot.expiry_date and lot.lot_id:
                        lot.lot_id.life_date = lot.expiry_date
                        lot.lot_id.use_date = lot.expiry_date
                pack.write({'qty_done': sum(pack.pack_lot_ids.mapped('qty'))})
        return {'type': 'ir.actions.act_window_close'}


class StockPackOperationLot(models.Model):
    _inherit = 'stock.pack.operation.lot'

    available_qty = fields.Integer(string="Available Qty")
