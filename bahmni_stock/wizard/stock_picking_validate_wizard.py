from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class StockPickingValidateWizard(models.TransientModel):
    _name = 'stock.picking.validate.wizard'
    _description = 'Validation Wizard for Stock Picking Operations'

    move_lines = fields.Many2many('stock.move.line', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Picking')
    picking_code = fields.Selection(related='picking_id.picking_type_id.code', readonly=True)
    source_location = fields.Many2one('stock.location', related='picking_id.location_id', string="Source Location",
                                      readonly=True)
    destination_location = fields.Many2one('stock.location', related='picking_id.location_dest_id',
                                           string="Destination Location", readonly=True)

    def btn_confirm(self):
        return self.picking_id.with_context(validation_confirmed=True).button_validate()
