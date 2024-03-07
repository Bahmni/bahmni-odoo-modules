from odoo import models, fields, api
from odoo.exceptions import MissingError
from psycopg2 import IntegrityError
import logging

_logger = logging.getLogger(__name__)
REQUIRED_KEYS = ['city_village','district','state','country','zip']

class District(models.Model):
    _name = 'district'
    _description = "Bahmni District"

    id = fields.Integer(string='District Id', required=True, readonly = True)
    name = fields.Char(string='Name', required=True)
    state = fields.Many2one('res.country.state',string='State', required=True)
    country = fields.Many2one('res.country',string='Country', required=True)

    @api.model
    def create(self, vals):
        try:
            country_name = vals.get('country')
            state_name = vals.get('state')
            state = self.env['res.country.state'].search([('name', '=ilike', state_name)], limit=1)
            country = self.env['res.country'].search([('name', '=ilike', country_name)], limit=1)
            if not state:
                raise MissingError(
                    _("State not found or already exists in the database. Please check your input or verify if the state already exists in the records."))
            if not country:
                raise MissingError(
                    _("Country not found or already exists in the database. Please check your input or verify if the country already exists in the records."))
            district_vals = {
                'name': vals.get('name'),
                'state': state.id,
                'country': country.id
            }
            return super(District, self).create(district_vals)
        except:
            raise Exception("Failed To Create District : {}".format(vals.get('name')))

class SubDistrict(models.Model):
    _name = 'sub.district'
    _description = "Bahmni Sub District"

    id = fields.Integer(string="Sub District Id", required=True, readonly = True)
    name = fields.Char(string='SubDistrict', required=True, index=True)
    district = fields.Many2one('district',string='District', required=True)
    state = fields.Many2one('res.country.state',string='State', required=True)
    country = fields.Many2one('res.country',string='Country', required=True)

    @api.model
    def create(self, vals):
        try:
            district = self._create_district(vals)
            sub_district_vals = {
                'name': vals.get('name'),
                'district': district.id,
                'state': district.state.id,
                'country': district.country.id
            }
            return super(SubDistrict, self).create(sub_district_vals)
        except:
            raise Exception("Failed To Create SubDistrict : {}".format(vals.get('name')))
    @api.model
    def _create_district(self, vals):
        district_name = vals.get('district')
        district = self.env['district'].search([('name', '=ilike', district_name)], limit=1)
        if not district:
            district_vals = {
                'name': district_name,
                'state': vals.get('state'),
                'country': vals.get('country')
            }
            district = self.env['district'].create(district_vals)
        return district

class CityVillage(models.Model):
    _name = "city.village"
    _description = "Bahmni City Village"
    _order = 'name'
    _rec_names_search = ['name', 'zipcode']

    id = fields.Integer(string="City Village Id", required=True, readonly = True)
    name = fields.Char(string='City Village', required=True, index=True)
    sub_district = fields.Many2one("sub.district", string='Sub District', required=False, domain="[('district', '=', id)]")
    district = fields.Many2one("district", string='District', required=True, domain="[('state', '=', id)]")
    state = fields.Many2one('res.country.state', string='State', required=True, domain="[('country', '=', id)]")
    country = fields.Many2one('res.country', string='Country', required=True)
    zip = fields.Char(string='ZIP / Postal Code', required=True)

    _sql_constraints = [
        ('zip_unique', 'UNIQUE(zip)', 'City / Village Zip code must be a unique value.'),
    ]

    @api.model
    def create(self, vals):
        try:
            city_village_vals = self._prepare_city_village_vals(vals)
            return super(CityVillage, self).create(city_village_vals)
        except Exception as error:
            raise Exception("Failed To Create City/Village : {}".format(vals.get('name')))

    def _prepare_city_village_vals(self, vals):
        sub_district_name = vals.get('sub_district')
        if sub_district_name:
            sub_district = self._create_sub_district(vals)
            city_village_vals = {
                'name': vals.get('name'),
                'sub_district': sub_district.id,
                'district': sub_district.district.id,
                'state': sub_district.state.id,
                'country': sub_district.country.id,
                'zip': vals.get('zip'),
            }
        else:
            district = self._create_district(vals)
            city_village_vals = {
                'name': vals.get('name'),
                'district': district.id,
                'state': district.state.id,
                'country': district.country.id,
                'zip': vals.get('zip'),
            }
        return city_village_vals
    @api.model
    def _create_sub_district(self, vals):
        sub_district_name = vals.get('sub_district')
        sub_district = self.env['sub.district'].search([('name', '=ilike', sub_district_name)], limit=1)
        if not sub_district:
            sub_district_vals = {
                'name': sub_district_name,
                'district': vals.get('district'),
                'state': vals.get('state'),
                'country': vals.get('country')
            }
            sub_district = self.env['sub.district'].create(sub_district_vals)
        return sub_district

    @api.model
    def _create_district(self, vals):
        district_name = vals.get('district')
        district = self.env['district'].search([('name', '=ilike', district_name)], limit=1)
        if not district:
            district_vals = {
                'name': district_name,
                'state': vals.get('state'),
                'country': vals.get('country')
            }
            district = self.env['district'].create(district_vals)
        return district

class AddressSeed(models.Model):
    _name = "address.seed"
    _description = "Bahmni Address Seed"
    _order = "id"
    id = fields.Integer(string="City Village Id", required=True, readonly = True)
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
            self._check_existing_city_village(vals)
            city_village_vals = self._prepare_city_village_values(vals)
            city_village = self.env['city.village'].create(city_village_vals)
            self._log_successful_creation(city_village)
        except Exception as error:
            self._handle_creation_failure(vals, error)
        return super(AddressSeed, self).create(vals)

    def _check_required_keys(self, vals):
        for required_key in REQUIRED_KEYS:
            if required_key not in vals:
                raise Exception("Missing required value for {} field in address.seed.csv. Exception found for City/Village {}".format(*(required_key, vals.get('city_village'))))

    def _check_existing_city_village(self, vals):
        city_village = self.env['city.village'].search([('zip', '=ilike', vals.get('zip'))], limit=1)
        if city_village:
            vals.update({'status': False})
            raise Exception("Failed To Create City/Village {} As City/Village With Same ZIP Code Already Exists.".format(vals.get('city_village')))

    def _prepare_city_village_values(self, vals):
        return {
            'name': vals.get('city_village'),
            'sub_district': vals.get('sub_district', ''),
            'district': vals.get('district'),
            'state': vals.get('state'),
            'country': vals.get('country'),
            'zip': vals.get('zip'),
        }

    def _log_successful_creation(self, city_village):
        _logger.info("City/Village %s - District %s - State %s Successfully Created.",city_village.name, city_village.district.name, city_village.state.name)

    def _handle_creation_failure(self, vals, error):
        vals.update({'status': False})
        _logger.error("Failed To Create Address Seed. {}".format(error))