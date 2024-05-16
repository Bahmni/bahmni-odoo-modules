from odoo import models, fields


class SyncableUnitsMapping(models.Model):
    _name = 'syncable.units.mapping'
    _description = "Units allowed to Sync mapped to Odoo Unit of Measures"

    name = fields.Char(string="Bahmni Unit Name", required=True)
    unit_of_measure = fields.Many2one('uom.uom', string="Odoo Unit of measure")
