from odoo import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    
