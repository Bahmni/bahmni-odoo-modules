from . import models
from odoo import api, SUPERUSER_ID

def _create_demo_config_param(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].set_param('odoo10_data_import.admin', 'admin')
