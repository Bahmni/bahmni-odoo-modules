from odoo import api, fields, models, _


class StockPickingValidateWizard(models.TransientModel):
    _name = 'stock.picking.validate.wizard'
    _description = 'Validation Wizard for Stock Picking Operations'

    move_lines = fields.Many2many('stock.move.line', readonly=True)

    def btn_confirm(self):
        return True
