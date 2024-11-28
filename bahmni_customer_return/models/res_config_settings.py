from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
	_inherit = "res.config.settings"
	
	allowed_days = fields.Integer(string="Maximum days limit for customer return",
		config_parameter="bahmni_auto_customer_return.no_of_days_threshold")

	def set_values(self):
		res = super(ResConfigSettings, self).set_values()
		self.env['ir.config_parameter'].sudo().set_param('bahmni_auto_customer_return.no_of_days_threshold',
														 self.allowed_days)
		return res

	@api.model
	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		ICPSudo = self.env['ir.config_parameter'].sudo()
		res.update(
			allowed_days=ICPSudo.get_param('bahmni_auto_customer_return.no_of_days_threshold'),
		)
		return res
