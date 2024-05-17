from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    update_product_prices_on_po_confirmation = fields.Boolean(
        string="Update price details of the product on Purchase Order Confirmation",
        config_parameter="bahmni_purchase.update_product_prices_on_po_confirm")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('bahmni_purchase.update_product_prices_on_po_confirm',
                                                         self.update_product_prices_on_po_confirmation)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            update_product_prices_on_po_confirmation=ICPSudo.get_param('bahmni_purchase.update_product_prices_on_po_confirm'),
        )
        return res
