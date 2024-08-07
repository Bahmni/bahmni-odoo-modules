
import datetime
from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    sale_price = fields.Float(string="Sale Price", digits='Product Price')
    mrp = fields.Float(string="MRP", digits='Product Price')
    cost_price = fields.Float(string="Cost Price", digits='Product Price')
    balance = fields.Float(string="Balance")
    existing_lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('company_id', '=', company_id)]", check_company=True)
    is_move_line_lot_expiring_soon = fields.Boolean(string="Is Lot Expiring Soon", readonly=True,
                                                    compute='is_lot_expiring_soon', default=False)

    @api.onchange('product_id','qty_done')
    def _onchange_balance_qty(self):
        if self.location_id and self.product_id:
            self.balance = (sum([stock.inventory_quantity_auto_apply for stock in self.env['stock.quant'].search([('location_id', '=', self.location_id.id),('product_id', '=', self.product_id.id)])])) - self.qty_done

    @api.onchange('existing_lot_id')
    def _onchange_existing_lot_id(self):
        if self.existing_lot_id:
           self.lot_name = self.existing_lot_id.name
           self.expiration_date = self.existing_lot_id.expiration_date
        else:
            self.lot_name = ''
            self.expiration_date = fields.Datetime.today() + datetime.timedelta(days=self.product_id.expiration_time)

    @api.constrains('mrp')
    def _check_fields_values(self):
        for rec in self:
            if rec.mrp > 0.00:
                if rec.sale_price > rec.mrp:
                    raise ValidationError('Sales Price should not be greater than MRP Rate.')
            else:
                pass

    @api.onchange('cost_price')
    def _check_cost_price_values(self):
        if self.cost_price > 0.00:
            self.sale_price = self.env['price.markup.table'].calculate_price_with_markup(self.cost_price)

    @api.model
    def default_get(self, fields):
        res = super(StockMoveLine, self).default_get(fields)
        move_ids = self.env['stock.move'].search([('picking_id', '=', res.get('picking_id')),('product_id', '=', res.get('product_id'))],limit=1)
        associated_purchase_line = move_ids.purchase_line_id
        if associated_purchase_line:
            product_default_uom=self.env['product.product'].search([('id', '=', res.get('product_id'))],limit=1).product_tmpl_id.uom_id
            res.update({'mrp': associated_purchase_line.product_uom._compute_price(associated_purchase_line.mrp, product_default_uom)})
            total_cost_value = associated_purchase_line.price_unit + (associated_purchase_line.price_tax / associated_purchase_line.product_qty)
            cost_value_per_unit = associated_purchase_line.product_uom._compute_price(total_cost_value, product_default_uom)
            if cost_value_per_unit > 0.00:
                res.update({'cost_price': cost_value_per_unit,
                            'sale_price': self.env['price.markup.table'].calculate_price_with_markup(cost_value_per_unit)
                            })
            else:
                pass
        return res

    # This function is overridden to set price details for the lot to help markup feature.
    # This will be called on receive products
    def _get_value_production_lot(self):
        res = super(StockMoveLine,self)._get_value_production_lot()
        res.update({
            'cost_price': self.cost_price,
            'sale_price': self.sale_price,
            'mrp': self.mrp
        })
        return res

    # Customisations to show warning when expiry of lot is within 30 days
    @api.depends('expiration_date')
    def is_lot_expiring_soon(self):
        for line in self:
            if line.expiration_date and self._compute_days_for_expiry(line.expiration_date) < 30:
                line.is_move_line_lot_expiring_soon = True
            else:
                line.is_move_line_lot_expiring_soon = False

    def _compute_days_for_expiry(self, expiration_date):
        return (expiration_date.date() - fields.Date.context_today(self)).days

    def move_line_warning(self):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Lot Expiry Warning'),
                'type': 'warning',
                'message': "Lot %s for %s expires in %s days" % (self.lot_id.name if self.lot_id else self.lot_name,
                                                                 self.product_id.name,
                                                                 self._compute_days_for_expiry(self.expiration_date))
            }
        }
        return notification
