from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
   
    sale_price_markup = fields.Boolean(string="Sale Price Markup Rule", store=True)


    
    def set_values(self):
       res = super(ResConfigSettings, self).set_values()
       self.env['ir.config_parameter'].sudo().set_param('discount.sale_price_markup', self.sale_price_markup)
       return res
    @api.model
    def get_values(self):
       res = super(ResConfigSettings, self).get_values()
       ICPSudo = self.env['ir.config_parameter'].sudo()
       res.update(
           sale_price_markup=ICPSudo.get_param('discount.sale_price_markup'),
       )
       return res
