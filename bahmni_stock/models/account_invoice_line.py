# -*- coding: utf-8 -*-
from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    # these fields are added here, as there is no dependency of stock in account module, 
    # but there is dependency of account in stock
    lot_id = fields.Many2one('stock.lot', string="Batch Name")
    expiry_date = fields.Datetime(string="Expiry Date")

