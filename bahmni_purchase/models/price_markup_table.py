from odoo import fields, models
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError, AccessError, RedirectWarning


class PriceMarkupTable(models.Model):
    _name = 'price.markup.table'

    lower_price = fields.Float(string="Lower Price", default=1)
    higher_price = fields.Float(string="Higher Price", default=1)
    markup_percentage = fields.Float(string="Markup Percentage", default=1)

    @api.constrains('lower_price', 'higher_price')
    def _check_fields_values(self):        
        if self.lower_price > self.higher_price:
            raise ValidationError('Lower Price should not be greater than Higher Price.')
        # Add any other conditions you need to check        
        for data in self.env['price.markup.table'].search([]):           
            if data.lower_price <= self.lower_price <= data.higher_price and data.id != self.id:
                raise ValidationError('Your lower price is available within the range of Lower Price and Higher Price of previous records.')
                
            if data.higher_price <= self.higher_price <= data.higher_price and data.id != self.id:
                raise ValidationError('Your higher price is available within the range of Lower Price and Higher Price of previous records.')
                
