from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class PriceMarkupTable(models.Model):
    _name = 'price.markup.table'

    lower_price = fields.Float(string="Minimum Cost", default=1)
    higher_price = fields.Float(string="Maximum Cost", default=1)
    markup_percentage = fields.Float(string="Markup Percentage", default=1)

    @api.constrains('lower_price', 'higher_price','markup_percentage')
    def _check_fields_values(self):
        if self.lower_price < 0 or self.higher_price < 0 or self.markup_percentage < 0:
            raise ValidationError('Negative values are not allowed for Minimum Cost, Maximum Cost and Markup Percentage.')

        if self.markup_percentage > 100:
            raise ValidationError('Markup percentage should not exceed 100%. Please enter a valid markup percentage.')

        if self.lower_price >= self.higher_price:
            raise ValidationError('Minimum cost should not be greater than maximum cost.')
        # Add any other conditions you need to check
        for data in self.env['price.markup.table'].search([]):
            if data.lower_price < self.lower_price < data.higher_price and data.id != self.id:
                raise ValidationError('Your minimum cost is available within the range of minimum cost and maximum cost of previous records.')

            if data.lower_price < self.higher_price < data.higher_price and data.id != self.id:
                raise ValidationError('Your maximum cost is available within the range of minimum cost and maximum cost of previous records.')

            if self.lower_price < data.lower_price < self.higher_price and data.id != self.id:
                raise ValidationError('Your minimum cost is available within the range of minimum cost and maximum cost of previous records.')

    def calculate_price_with_markup(self, price):
        markup_table_line = self.search([('lower_price', '<', price),
                                        '|', ('higher_price', '>=', price),
                                        ('higher_price', '=', 0)], limit=1)
        if markup_table_line:
            return price + (price * markup_table_line.markup_percentage / 100)
        else:
            return price


