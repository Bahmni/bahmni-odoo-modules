from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    is_auto_payment_allocation_enabled = fields.Boolean(
        string="Enable auto allocation of payments and credits to outstanding invoices",
        config_parameter="bahmni_auto_payment_reconciliation.enabled")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('bahmni_auto_payment_reconciliation.enabled',
                                                         self.is_auto_payment_allocation_enabled)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        res.update(
            is_auto_payment_allocation_enabled=ICPSudo.get_param('bahmni_auto_payment_reconciliation.enabled'),
        )
        return res
