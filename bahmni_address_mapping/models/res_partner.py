from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    village_id = fields.Many2one('village.village', string="Village")
    subdistrict_id = fields.Many2one("district.subdistrict", string="Sub-District")
    district_id = fields.Many2one('state.district', string="District")

    @api.onchange('village_id')
    def onchange_village_id(self):
        if self.village_id:
            self.district_id = self.village_id.district_id.id
            self.subdistrict_id = self.village_id.subdistrict_id.id
            self.state_id = self.village_id.state_id.id
            self.country_id = self.village_id.country_id.id
            return {'domain': {'subdistrict_id': [('id', '=', self.village_id.subdistrict_id.id)],
                               'state_id': [('id', '=', self.village_id.state_id.id)],
                               'district_id': [('id', '=', self.village_id.district_id.id)],
                               'country_id': [('id', '=', self.village_id.country_id.id)]}}
        else:
            return {'domain': {'subdistrict_id': [],
                               'state_id': [],
                               'district_id': [],
                               'country_id': []}}
