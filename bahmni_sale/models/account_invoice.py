from odoo import fields, models, api

class AccountInvoice(models.Model):
    _inherit = 'account.move'
	
    shop_id = fields.Many2one('sale.shop', 'Shop')


