from odoo import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    
    # Batch tracking fields for pharmaceutical inventory
    lot_id = fields.Many2one('stock.lot', string="Batch Name")
    expiry_date = fields.Datetime(string="Expiry Date")

