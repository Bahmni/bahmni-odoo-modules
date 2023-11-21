# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import json
import uuid

STATE_CODE_PREFIX = 'UNKNOWN-'
_logger = logging.getLogger(__name__)


class ApiEventWorker(models.Model):
    _name = 'api.event.worker'
    _auto = False

    @api.model
    def process_event(self, vals):
        '''Method getting triggered from Bahmni side'''
        _logger.info("vals")
        _logger.info(vals)
        category = vals.get("category")
        try:
            if category == "create.customer":
                self._create_or_update_customer(vals)
                return "The customer have been successfully created / updated."
            elif category == "create.sale.order":
                self.env['order.save.service'].create_orders(vals)
                return "Sale order has been created successfully."
            elif category == "create.drug":
                self.env['drug.data.service'].create_or_update_drug(vals)
                return "The drug have been successfully created / updated."
            else:
                raise UserError("Integration process is not defined. Kindly contact ERP tech team for support.")
        except Exception as err:
            _logger.info("\n Processing event threw error: %s", err)
            raise

    @api.model
    def _create_or_update_customer(self, vals):
        patient_ref = vals.get("ref")
        customer_vals = self._get_customer_vals(vals)
        # removing null values, as while updating null values in write method will remove old values

        for rec in customer_vals.keys():
            if not customer_vals[rec]:
                del customer_vals[rec]
        existing_customer = self.env['res.partner'].sudo().search([('ref', '=', patient_ref)])
        if existing_customer:
            existing_customer.write(customer_vals)
            self._create_or_update_person_attributes(existing_customer.id,vals)
        else:
            customer = self.env['res.partner'].sudo().create(customer_vals)
            self._create_or_update_person_attributes(customer.id,vals)

    @api.model
    def _get_address_details(self, address):
        res = {}
        if address.get('address1'):
            res.update({'street': address['address1']})
        if address.get('address2'):
            res.update({'street2': address['address2']})

        auto_create_customer_address_levels =  True
        country = self._find_country(address)
        state = None
        district = None
        if address.get("stateProvince") and country:
            state = self._find_or_create_state(country, address['stateProvince'], auto_create_customer_address_levels)
            if state:
                res.update({'state_id': state.id})

        if address.get('countyDistrict') and state:
            district = self._find_or_create_district(country, state, address.get('countyDistrict'), auto_create_customer_address_levels)
            if district:
                res.update({'district_id': district.id})

        # for now, from bahmni side, Taluka is sent as address3
        if address.get('address3') and district:
            # =ilike operator will ignore the case of letters while comparing
            tehsil = self._find_or_create_level3(state, district, address['address3'], auto_create_customer_address_levels)
            if tehsil:
                res.update({'tehsil_id': tehsil.id})

        return res

    @api.model
    def _find_country(self, address):
        return self.env['res.company'].sudo().search([('id', '=', 2)]).partner_id.country_id

    @api.model
    def _find_or_create_level3(self, state, district, level_name, auto_create_customer_address_levels):
        levels = self.env['district.tehsil'].search([('name', '=ilike', level_name),
                                                    ('district_id', '=', district.id if district else False)])
        if not levels and auto_create_customer_address_levels:
            level = self.env['district.tehsil'].create({'name': level_name,
                                                        'district_id': district.id if district else False,
                                                        'state_id': state.id if state else False})
        else:
            level = levels[0]
        return level

    @api.model
    def _find_or_create_district(self, country, state, district_county_name, auto_create_customer_address_levels):
        districts = self.env['state.district'].search([('name', '=ilike', district_county_name),
                                                      ('state_id', '=', state.id if state else None)])
        if not districts and auto_create_customer_address_levels:
            district = self.env['state.district'].create({'name': district_county_name,
                                                          'state_id': state.id if state else None,
                                                          'country_id': country.id})
        else:
            district = districts[0]
        return district

    @api.model
    def _find_or_create_state(self, country, state_province_name, auto_create_customer_address_levels):
        states = self.env['res.country.state'].search([('name', '=ilike', state_province_name),
                                                      ('country_id', '=', country.id)])
        if not states and auto_create_customer_address_levels == '1':
            state_code = STATE_CODE_PREFIX + str(uuid.uuid4())
            state = self.env['res.country.state'].create({'name': state_province_name,
                                                          'code': state_code,
                                                          'country_id': country.id})
        else:
            state = False
        return state

    def _get_customer_vals(self, vals):
        res = {}
        res.update({'ref': vals.get('ref'),
                    'name': vals.get('name'),
                    'local_name': vals.get('local_name'),
                    'uuid': vals.get('uuid')})
        address_data = vals.get('preferredAddress')
        # get validated address details
        address_details = self._get_address_details(json.loads(address_data))
        # update address details
        res.update(address_details)
        # update other details : for now there is only scope of updating contact.
        if vals.get('primaryContact'):
            res.update({'phone': vals['primaryContact']})
        return res
        
    def _create_or_update_person_attributes(self, cust_id, vals):
        attributes = json.loads(vals.get("attributes", "{}"))
        if vals.get('village'):
            village_master = self.env['village.village']
            customer_master = self.env['res.partner'].sudo().search([('id', '=', cust_id)])
            identified_village = village_master.sudo().search([('name', '=', vals.get('village'))], limit=1)
            if identified_village and customer_master:
                customer_master.village_id = identified_village.id
            else:
                created_village = village_master.sudo().create({'name': vals.get('village')})
                customer_master.village_id = created_village.id

        for key in attributes:
            if key in [key for key in attributes]:
                column_dict = {'partner_id': cust_id}
                existing_attribute = self.env['res.partner.attributes'].sudo().search([('partner_id', '=', cust_id),('name', '=', key)])
                if any(existing_attribute):
                    existing_attribute.unlink()
                column_dict.update({"name": key, "value" : attributes[key]})
                self.env['res.partner.attributes'].sudo().create(column_dict)
