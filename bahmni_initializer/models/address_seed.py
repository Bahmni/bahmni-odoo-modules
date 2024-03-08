from odoo import models, fields, api
from odoo.exceptions import MissingError
from psycopg2 import IntegrityError
import logging

_logger = logging.getLogger(__name__)
REQUIRED_KEYS = ['city_village','district','state','country','zip']

class District(models.Model):
    _name = 'district'
    _description = "Bahmni District"

    id = fields.Integer(string='District Id', required=True, readonly=True)
    name = fields.Char(string='District', required=True)
    state = fields.Many2one('res.country.state', string='State', required=True)
    country = fields.Many2one('res.country', string='Country', required=True)

    @api.onchange('state')
    def onchange_state(self):
        domain = []
        if self.state:
            self.country = self.state.country_id.id
            domain = [('id', '=', self.state.country_id.id)]
        return {'domain': {'country_id': domain}}

class SubDistrict(models.Model):
    _name = 'sub.district'
    _description = "Bahmni Sub District"

    id = fields.Integer(string="Sub District Id", required=True, readonly=True)
    name = fields.Char(string='Sub District', required=True, index=True)
    district = fields.Many2one('district', string='District', required=True)
    state = fields.Many2one('res.country.state', string='State', required=True)
    country = fields.Many2one('res.country', string='Country', required=True)

    @api.onchange('district', 'state')
    def onchange_district_state(self):
        domain = {}
        if self.district:
            self.state = self.district.state.id
            domain.update({'state': [('id', '=', self.district.state.id)]})
        if self.state:
            if not self.district or self.state.id != self.district.state.id:
                self.district = False
                district_domain = [('state', '=', self.state.id)]
                domain.update({'district': district_domain})
            self.country = self.state.country_id.id
            domain.update({'country': [('id', '=', self.state.country_id.id)]})
        return {'domain': domain}

class CityVillage(models.Model):
    _name = "city.village"
    _description = "Bahmni City Village"
    _order = 'name'
    _rec_names_search = ['name', 'zipcode']

    id = fields.Integer(string="City Village Id", required=True, readonly=True)
    name = fields.Char(string='City Village', required=True, index=True)
    sub_district = fields.Many2one("sub.district", string='Sub District', required=False)
    district = fields.Many2one("district", string='District', required=True)
    state = fields.Many2one('res.country.state', string='State', required=True)
    country = fields.Many2one('res.country', string='Country', required=True)
    zip = fields.Char(string='ZIP / Postal Code', required=True)

    _sql_constraints = [
        ('zip_unique', 'UNIQUE(zip)', 'City / Village Zip code must be a unique value.'),
    ]

    @api.model
    def create(self, vals):
        try:
            self._check_existing_zip(vals)
            return super(CityVillage, self).create(vals)
        except Exception as error:
            raise Exception("Failed To Create City/Village : {}".format(vals.get('name')))

    @api.onchange('sub_district', 'district', 'state')
    def onchange_district_state(self):
        domain = {}
        if self.sub_district:
            self.district = self.sub_district.district.id
            domain.update({'district': [('id', '=', self.sub_district.district.id)]})
        if self.district:
            self.state = self.district.state.id
            domain.update({'state': [('id', '=', self.district.state.id)]})
        if self.state:
            if not self.district or self.state.id != self.district.state.id:
                self.district = False
                district_domain = [('state', '=', self.state.id)]
                domain.update({'district': district_domain})
            self.country = self.state.country_id.id
            domain.update({'country': [('id', '=', self.state.country_id.id)]})
        return {'domain': domain}

    def _check_existing_zip(self, vals):
        city_village = self.env['city.village'].search([('zip', '=ilike', vals.get('zip'))], limit=1)
        if city_village:
            vals.update({'status': False})
            raise Exception("Failed To Create City/Village {} As City/Village With Same ZIP Code Already Exists.".format(vals.get('city_village')))

class AddressSeed(models.Model):
    _name = "address.seed"
    _description = "Bahmni Address Seed"
    _order = "id"

    id = fields.Integer(string="City Village Id", required=True, readonly=True)
    city_village = fields.Char(string='City Village', required=False, index=True)
    sub_district = fields.Char(string='Sub District', required=False)
    district = fields.Char(string='District', required=False)
    state = fields.Char(string='State', required=False)
    country = fields.Char(string='Country', required=False)
    zip = fields.Char(string='ZIP / Postal Code', required=False)
    status = fields.Boolean(string='Initialized', default=False, required=False)

    @api.model
    def create(self, vals):
        try:
            self._check_required_keys(vals)
            self._check_existing_zip(vals)
            city_village_vals = self._prepare_city_village_values(vals)
            city_village = self.env['city.village'].create(city_village_vals)
            self._log_successful_creation(city_village)
        except Exception as error:
            self._handle_creation_failure(vals, error)
        return super(AddressSeed, self).create(vals)

    def _check_required_keys(self, vals):
        required_keys = ['city_village', 'sub_district', 'district', 'state', 'country', 'zip']
        missing_keys = [key for key in required_keys if key not in vals]
        if missing_keys:
            raise Exception("Missing required value(s) for {} field(s) in address.seed.csv".format(', '.join(missing_keys)))

    def _check_existing_zip(self, vals):
        existing_city_village = self.env['city.village'].search([('zip', '=ilike', vals.get('zip'))], limit=1)
        if existing_city_village:
            raise Exception("Failed To Create City/Village {}. A City/Village With the Same ZIP Code Already Exists.".format(vals.get('city_village')))

    def _prepare_city_village_values(self, vals):
        district = self._get_or_create_district(vals)
        sub_district = self._get_or_create_sub_district(vals, district)
        state, country = self._get_state_and_country(vals)
        return {
            'name': vals.get('city_village'),
            'district': district.id,
            'sub_district': sub_district.id,
            'state': state.id,
            'country': country.id,
            'zip': vals.get('zip'),
        }

    def _get_or_create_sub_district(self, vals, district):
        sub_district_name = vals.get('sub_district')
        sub_district = self.env['sub.district'].search([('name', '=ilike', sub_district_name)], limit=1)
        if not sub_district:
            return self.env['sub.district'].create({
                'name': sub_district_name,
                'district': district.id,
                'state': district.state.id,
                'country': district.country.id
            })
        return sub_district

    def _get_or_create_district(self, vals):
        district_name = vals.get('district')
        district = self.env['district'].search([('name', '=ilike', district_name)], limit=1)
        if not district:
            state, country = self._get_state_and_country(vals)
            return self.env['district'].create({
                'name': district_name,
                'state': state.id,
                'country': country.id
            })
        return district

    def _get_state_and_country(self, vals):
        state_name = vals.get('state')
        country_name = vals.get('country')
        state = self.env['res.country.state'].search([('name', '=ilike', state_name)], limit=1)
        country = self.env['res.country'].search([('name', '=ilike', country_name)], limit=1)
        if not state:
            raise Exception("State '{}' Not Found.".format(state_name))
        if not country:
            raise Exception("Country '{}' Not Found.".format(country_name))
        return state, country

    def _log_successful_creation(self, city_village):
        _logger.info("City/Village %s - District %s - State %s Successfully Created.", city_village.name, city_village.district.name, city_village.state.name)

    def _handle_creation_failure(self, vals, error):
        vals.update({'status': False})
        _logger.error("Failed To Create Address Seed. {}".format(error))
