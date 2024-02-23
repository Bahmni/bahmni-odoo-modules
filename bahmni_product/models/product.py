from copy import copy
from datetime import datetime, date

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _inherit = 'product.product'



    stock_quant_ids = fields.One2many('stock.quant', 'product_id', help='Technical: used to compute quantities.')
    stock_move_ids = fields.One2many('stock.move', 'product_id', help='Technical: used to compute quantities.')
    actual_stock = fields.Integer(string="Actual Stock",
                                  help="Get the actual stock available for product."
                                  "\nActual stock of product doesn't eliminates the count of expired lots from available quantities.")
    mrp = fields.Float(string="MRP")    # when variants exists for product, then mrp will be defined at variant level.
    uuid = fields.Char(string="UUID", index='btree_not_null')
    
    free_qty = fields.Float(
        'Free To Use Quantity ', search='_search_free_qty',
        digits='Product Unit of Measure', compute_sudo=False,store=True,
        help="Forecast quantity (computed as Quantity On Hand "
             "- reserved quantity)\n"
             "In a context with a single Stock Location, this includes "
             "goods stored in this location, or any of its children.\n"
             "In a context with a single Warehouse, this includes "
             "goods stored in the Stock Location of this Warehouse, or any "
             "of its children.\n"
             "Otherwise, this includes goods stored in any Stock Location "
             "with 'internal' type.")

    _sql_constraints = [
        ('unique_uuid', 'UNIQUE(uuid)', 'UUID must be unique'),
    ]

    @api.model
    def create(self, vals):
        if self._context.get('create_from_tmpl'):
            if vals.get('product_tmpl_id') and vals.get('attribute_value_ids'):
                if not vals.get('attribute_value_ids')[0][2]:
                    vals.update({'mrp': self.env['product.template'].browse(vals.get('product_tmpl_id')).mrp})
        product = super(ProductProduct, self.with_context(create_product_product=True,
                                                          mrp=vals.get('mrp'))).create(vals)
        return product

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        if vals.get('mrp') and not self._context.get('write_through_tmpl'):
            if len(self.product_tmpl_id.product_variant_ids) == 1:
                self.product_tmpl_id.mrp = vals.get('mrp')
        return res

    def name_get(self):
        '''inherited this method to add category name as suffix to product name
    '''
        res = super(ProductProduct, self).name_get()
        result = []
        for r in res:
            categ_name = self.browse(r[0]).categ_id.name
            result.append((r[0], r[1] + ' ('+categ_name+')'))
        return result

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    




    uuid = fields.Char(string="UUID")
    mrp = fields.Float(string="MRP")
    manufacturer = fields.Many2one('res.partner', string="Manufacturer",
                                   domain=[('manufacturer', '=', True)])
    drug = fields.Char(string="Drug Name",
                       help="This field is for assigning Generic name to product")

    actual_stock = fields.Integer(string="Actual Stock", 
                                  help="Get the actual stock available for product."
                                  "\nActual stock of product doesn't eliminates the count of expired lots from available quantities.")
    
    free_qty = fields.Integer(string="Free Qty",
                                  help="Get the actual stock available for product."
                                  "\nActual stock of product doesn't eliminates the count of expired lots from available quantities.")
    
    dhis2_code = fields.Char(string="DHIS2 Code")


    @api.model
    def create(self, vals):
        # update mrp value in template, when template is getting created through product_product object
        if self._context.get('create_product_product'):
            vals.update({'mrp': self._context.get('mrp')})
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        '''this method is inherited to set mrp price in product.product record 
        when changed in product.template, in case of no variants defined'''
        self.ensure_one()
        res = super(ProductTemplate, self).write(vals)
        if vals.get('mrp'):
            if len(self.product_variant_ids) == 1:
                # context passed while calling write of product_product,
                # as write method of product_product is also overridden to do same thing, hence to avoid recursion
                self.product_variant_ids.with_context({'write_through_tmpl': True}).write({'mrp': vals.get('mrp')})
        return res
