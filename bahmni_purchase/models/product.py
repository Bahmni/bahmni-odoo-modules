from odoo import models, fields


class product_product(models.Model):
    _inherit = 'product.product'



    low_stock = fields.Boolean(string="Low Stock")
