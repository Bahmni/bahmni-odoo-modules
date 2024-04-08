from odoo import fields, models, api
import uuid
import logging

STATE_CODE_PREFIX = 'UNKNOWN-'
_logger = logging.getLogger(__name__)


class AddressMappingService(models.Model):
    _name = 'address.mapping.service'
    _auto = False
    auto_create_customer_address_levels = True

    @api.model
    def _map_address_fields(self, address):
        mapped_result = {'country_id': None, 'state_id': None, 'district_id': None, 'subdistrict_id': None,
                         'village_id': None, 'zip': None, 'street': None, 'street2': None}
        address_field_for_country = self._get_openmrs_address_field('country')
        address_field_for_state = self._get_openmrs_address_field('state')
        address_field_for_district = self._get_openmrs_address_field('district')
        address_field_for_subdistrict = self._get_openmrs_address_field('subdistrict')
        address_field_for_village = self._get_openmrs_address_field('village')
        address_field_for_zip = self._get_openmrs_address_field('zip')
        address_field_for_street = self._get_openmrs_address_field('street')
        address_field_for_street2 = self._get_openmrs_address_field('street2')

        # Mapping plain text field address fields
        if address_field_for_zip and address.get(address_field_for_zip):
            mapped_result.update({'zip': address.get(address_field_for_zip, '')})
        if address_field_for_street and address.get(address_field_for_street):
            mapped_result.update({'street': address.get(address_field_for_street, '')})
        if address_field_for_street2 and address.get(address_field_for_street2):
            mapped_result.update({'street2': address.get(address_field_for_street2, '')})

        # Mapping hierarchical address fields
        country = None
        state = None
        district = None
        subdistrict = None
        village = None
        if address_field_for_country:
            country_name = address.get(address_field_for_country)
            if country_name:
                country = self._find_country(country_name)
                if country:
                    mapped_result.update({'country_id': country.id})
                else:
                    _logger.warning(
                        'Country %s not found in the Odoo database', country_name)
            else:
                _logger.warning('Country value not passed in address with field %s', address_field_for_country)

        if address_field_for_state:
            state_province_name = address.get(address_field_for_state)
            if state_province_name:
                state = self._find_or_create_state(country, state_province_name,
                                                   self.auto_create_customer_address_levels)
                if state:
                    mapped_result.update({'state_id': state.id})
                    if not country:
                        _logger.info("Mapping country from state to customer address")
                        country = state.country_id
                        mapped_result.update({'country_id': state.country_id.id})
                else:
                    _logger.warning('State %s not found/created in the Odoo database', state_province_name)
            else:
                _logger.warning('State value not passed in address with field %s', address_field_for_state)

        if address_field_for_district:
            district_name = address.get(address_field_for_district)
            if district_name:
                district = self._find_or_create_district(country, state, district_name,
                                                         self.auto_create_customer_address_levels)
                if district:
                    mapped_result.update({'district_id': district.id})
                else:
                    _logger.warning('District %s not found/created in the Odoo database', district_name)
            else:
                _logger.warning('District value not passed in address with field %s', address_field_for_district)

        if address_field_for_subdistrict:
            subdistrict_name = address.get(address_field_for_subdistrict)
            if subdistrict_name:
                subdistrict = self._find_or_create_subdistrict(country, state, district, subdistrict_name,
                                                               self.auto_create_customer_address_levels)
                if subdistrict:
                    mapped_result.update({'subdistrict_id': subdistrict.id})
                else:
                    _logger.warning('Subdistrict %s not found/created in the Odoo database', subdistrict_name)
            else:
                _logger.warning('Subdistrict value not passed in address with field %s', address_field_for_subdistrict)

        if address_field_for_village:
            village_name = address.get(address_field_for_village)
            if village_name:
                village = self._find_or_create_village(country, state, district, subdistrict, village_name,
                                                       self.auto_create_customer_address_levels)
                if village:
                    mapped_result.update({'village_id': village.id})
                else:
                    _logger.warning('Village %s not found/created in the Odoo database', village_name)
            else:
                _logger.warning('Village value not passed in address with field %s', address_field_for_village)

        _logger.info('Input address: %s', str(address))
        _logger.info('Mapped address: %s', str(mapped_result))
        return mapped_result

    def _get_openmrs_address_field(self, odoo_field_name):
        return self.env['address.mapping.table'].search([('odoo_address_field', '=', odoo_field_name)],
                                                        limit=1).openmrs_address_field


    @api.model
    def _find_country(self, country_name):
        return self.env['res.country'].search([('name', '=ilike', country_name)], limit=1)

    @api.model
    def _find_or_create_state(self, country, state_province_name, auto_create_customer_address_levels):

        if country:
            _logger.info('Finding state entry for %s for country %s', state_province_name, country.name)
            state = self.env['res.country.state'].search([('name', '=ilike', state_province_name),
                                                          ('country_id', '=', country.id)], limit=1)
            if state:
                _logger.info('State %s found in the Odoo database', state_province_name)
                return state

        _logger.info('Country not mapped. Searching with only state name %s', state_province_name)
        state = self.env['res.country.state'].search([('name', '=ilike', state_province_name)], limit=1)
        if state:
            _logger.info('State %s found in the Odoo database', state_province_name)
            return state

        if country and auto_create_customer_address_levels:
            _logger.info("Creating new state %s for country %s", state_province_name, country.name)
            state_code = STATE_CODE_PREFIX + str(uuid.uuid4())
            state = self.env['res.country.state'].create({'name': state_province_name,
                                                          'code': state_code,
                                                          'country_id': country.id})
            return state
        else:
            _logger.info(
                "Country is not defined or address auto creation is disabled. Returning None for State mapping")
            return None

    @api.model
    def _find_or_create_district(self, country, state, district_name, auto_create_customer_address_levels):

        _logger.info('Finding district entry for %s with state %s, country %s',
                     district_name,
                     state.name if state else 'None',
                     country.name if country else 'None')
        districts = self.env['state.district'].search([('name', '=ilike', district_name),
                                                       ('state_id', '=', state.id if state else None),
                                                       ('country_id', '=', country.id if country else None)])

        if districts:
            if len(districts) == 1:
                _logger.info('Unique District %s found in the Odoo database', district_name)
                return districts[0]
            else:
                _logger.warning(
                    'Multiple districts found with name %s. Returning None for district mapping', district_name)
                return None

        if auto_create_customer_address_levels:
            _logger.info('Cresting new district entry for %s with state %s, country %s',
                         district_name,
                         state.name if state else 'None',
                         country.name if country else 'None')
            district = self.env['state.district'].create({'name': district_name,
                                                          'state_id': state.id if state else None,
                                                          'country_id': country.id if country else None})
            return district
        else:
            _logger.info("Address auto creation is disabled. Returning None for District mapping")
            return None

    @api.model
    def _find_or_create_subdistrict(self, country, state, district, subdistrict_name,
                                    auto_create_customer_address_levels):
        _logger.info('Finding subdistrict entry for %s with district %s, state %s, country %s',
                     subdistrict_name,
                     district.name if district else 'None',
                     state.name if state else 'None',
                     country.name if country else 'None')
        subdistricts = self.env['district.subdistrict'].search([('name', '=ilike', subdistrict_name),
                                                                (
                                                                    'district_id', '=',
                                                                    district.id if district else False),
                                                                ('state_id', '=', state.id if state else False),
                                                                ('country_id', '=',
                                                                 country.id if country else False)])
        if subdistricts:
            if len(subdistricts) == 1:
                _logger.info('Unique Subdistrict %s found in the Odoo database', subdistrict_name)
                return subdistricts[0]
            else:
                _logger.warning(
                    'Multiple subdistricts entry for %s with district %s, state %s, country %s', subdistrict_name,
                    district.name, state.name, country.name)
                return None

        if auto_create_customer_address_levels:
            _logger.info('Creating new subdistrict entry for %s with district %s, state %s, country %s',
                         subdistrict_name,
                         district.name if district else 'None',
                         state.name if state else 'None',
                         country.name if country else 'None')
            subdistrict = self.env['district.subdistrict'].create({'name': subdistrict_name,
                                                                   'district_id': district.id if district else None,
                                                                   'state_id': state.id if state else None,
                                                                   'country_id': country.id if country else None})
            return subdistrict
        else:
            _logger.info("Address auto creation is disabled. Returning None for Subdistrict mapping")
            return None

    @api.model
    def _find_or_create_village(self, country, state, district, subdistrict, village_name,
                                auto_create_customer_address_levels):
        _logger.info(
            'Finding village entry for %s with subdistrict %s, district %s, state %s, country %s',
            village_name,
            subdistrict.name if subdistrict else 'None',
            district.name if district else 'None',
            state.name if state else 'None',
            country.name if country else 'None')

        villages = self.env['village.village'].search(
            [('name', '=ilike', village_name),
             ('subdistrict_id', '=', subdistrict.id if subdistrict else False),
             ('district_id', '=', district.id if district else False),
             ('state_id', '=', state.id if state else False),
             ('country_id', '=', country.id if country else False)])
        if villages:
            if len(villages) == 1:
                _logger.info('Unique Village %s found in the Odoo database', village_name)
                return villages[0]
            else:
                _logger.warning(
                    'Multiple village entry for %s with subdistrict %s, district %s, state %s, country %s',
                    village_name,
                    subdistrict.name if subdistrict else 'None',
                    district.name if district else 'None',
                    state.name if state else 'None',
                    country.name if country else 'None')
                return None
        if auto_create_customer_address_levels:
            _logger.info(
                'Creating new village entry for %s with subdistrict %s, district %s, state %s, country %s',
                village_name,
                subdistrict.name if subdistrict else 'None',
                district.name if district else 'None',
                state.name if state else 'None',
                country.name if country else 'None')
            village = self.env['village.village'].create({'name': village_name,
                                                          'subdistrict_id': subdistrict.id if subdistrict else None,
                                                          'district_id': district.id if district else None,
                                                          'state_id': state.id if state else None,
                                                          'country_id': country.id if country else None})
            return village
        else:
            _logger.info("Address auto creation is disabled. Returning None for Village mapping")
            return None
