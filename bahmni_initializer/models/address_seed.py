from odoo import models, fields, api
from odoo.exceptions import MissingError
from psycopg2 import IntegrityError
import logging

_logger = logging.getLogger(__name__)
REQUIRED_KEYS = ['city_village','district','state','country']

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
    is_initialized = fields.Boolean(string='Initialized', default=False, required=False)
    init_error_message = fields.Char(string='Reason for Initialization Failure', required=False)

    @api.model
    def create(self, vals):
        try:
            self._check_required_keys(vals)
            address_seed = self._check_for_duplicate(vals)
            if address_seed:
               return address_seed
            city_village_vals = self._prepare_city_village_values(vals)
            city_village = self.env['village.village'].create(city_village_vals)
            vals.update({'is_initialized': True})
            self._log_successful_creation(city_village)
        except Exception as error:
            vals.update({'init_error_message': error, 'is_initialized': True})
            self._handle_creation_failure(vals, error)
        return super(AddressSeed, self).create(vals)

    def _check_for_duplicate(self, vals):
        address_seed = self.env['address.seed'].search([('city_village', '=ilike', vals.get('city_village')),
                                                        ('sub_district', '=ilike', vals.get('sub_district')),
                                                        ('district', '=ilike', vals.get('district')),
                                                        ('state', '=ilike', vals.get('state')),
                                                        ('country', '=ilike', vals.get('country'))], limit=1)
        return address_seed

    def _check_required_keys(self, vals):
        missing_fields = [key for key in REQUIRED_KEYS if key not in vals or not vals.get(key)]
        if missing_fields:
            raise Exception("Missing required value(s) for {} field(s) in address.seed.csv".format(', '.join(missing_fields)))

    def _prepare_city_village_values(self, vals):
        district = self._get_or_create_district(vals)
        sub_district = self._get_or_create_sub_district(vals, district)
        return {
            'name': vals.get('city_village'),
            'district_id': district.id,
            'subdistrict_id': sub_district.id,
            'state_id': district.state_id.id,
            'country_id': district.country_id.id
        }

    def _get_or_create_sub_district(self, vals, district):
        sub_district_name = vals.get('sub_district')
        sub_district = self.env['district.subdistrict'].search([('name', '=ilike', sub_district_name)], limit=1)
        if not sub_district:
            return self.env['district.subdistrict'].create({
                'name': sub_district_name,
                'district_id': district.id,
                'state_id': district.state_id.id,
                'country_id': district.country_id.id
            })
        return sub_district

    def _get_or_create_district(self, vals):
        district_name = vals.get('district')
        district = self.env['state.district'].search([('name', '=ilike', district_name)], limit=1)
        if not district:
            state, country = self._get_state_and_country(vals)
            return self.env['state.district'].create({
                'name': district_name,
                'state_id': state.id,
                'country_id': country.id
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
        _logger.info("City/Village %s - District %s - State %s Successfully Created.", city_village.name, city_village.district_id.name, city_village.state_id.name)

    def _handle_creation_failure(self, vals, error):
        _logger.error("Failed To Create Address Seed. {}".format(error))
