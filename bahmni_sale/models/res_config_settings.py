from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
   
    is_delivery_automated = fields.Boolean(string="Enable auto delivery on sale order confirm action", config_parameter="bahmni_sale.is_delivery_automated")
    sale_price_markup = fields.Boolean(string="Sale Price Markup Rule", config_parameter="bahmni_sale.sale_price_markup" )
    is_invoice_automated = fields.Boolean(string="Enable auto invoice on sale order confirm action", config_parameter="bahmni_sale.is_invoice_automated")
    allocate_quantity_from_multiple_batches = fields.Boolean(string="Allocate quantity from multiple batches", config_parameter="bahmni_sale.allocate_quantity_from_multiple_batches")

    group_final_so_charge = fields.Boolean(string="Allow to enter final Sale Order charge",
                                           implied_group='bahmni_sale.group_allow_change_so_charge')
    group_default_quantity = fields.Boolean(string="Allow to enter default quantity as -1",
                                            implied_group='bahmni_sale.group_allow_change_qty')
    convert_dispensed = fields.Boolean(string="Allow to automatically convert "
                                       "quotation to sale order if drug is dispensed from local shop")
    validate_picking = fields.Boolean(string="Validate delivery when order confirmed")
    allow_negative_stock = fields.Boolean(string="Allow negative stock")
    auto_invoice_dispensed = fields.Boolean(string="Automatically register payment for dispensed order invoice")
    auto_create_customer_address_levels = fields.Boolean(string="Automatically create customer address for state, district, level3")


    
    def set_values(self):
       res = super(ResConfigSettings, self).set_values()
       self.env['ir.config_parameter'].sudo().set_param('bahmni_sale.sale_price_markup', self.sale_price_markup)
       self.env['ir.config_parameter'].sudo().set_param('bahmni_sale.is_delivery_automated', self.is_delivery_automated)
       self.env['ir.config_parameter'].sudo().set_param('bahmni_sale.is_invoice_automated', self.is_invoice_automated)
       self.env['ir.config_parameter'].sudo().set_param('bahmni_sale.allocate_quantity_from_multiple_batches', self.allocate_quantity_from_multiple_batches)
       return res
    @api.model
    def get_values(self):
       res = super(ResConfigSettings, self).get_values()
       ICPSudo = self.env['ir.config_parameter'].sudo()
       res.update(
           sale_price_markup=ICPSudo.get_param('bahmni_sale.sale_price_markup'),
           is_delivery_automated=ICPSudo.get_param('bahmni_sale.is_delivery_automated'),
           is_invoice_automated=ICPSudo.get_param('bahmni_sale.is_invoice_automated'),
           allocate_quantity_from_multiple_batches=ICPSudo.get_param('bahmni_sale.allocate_quantity_from_multiple_batches'),
       )
       return res
