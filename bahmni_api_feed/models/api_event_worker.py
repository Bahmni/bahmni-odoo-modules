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
        category = vals.get("category")
        try:
            if category == "create.customer":
                self._create_or_update_customer(vals)
            return {'success': True}    
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

        return res


    def _get_customer_vals(self, vals):
        res = {}
        res.update({'ref': vals.get('ref'),
                    'name': vals.get('name'),
                    'local_name': vals.get('local_name'),
                    'uuid': vals.get('uuid'),
                    })
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
        customer = self.env['res.partner'].sudo().search([('id', '=', cust_id)])
        if vals['village']:
            customer.village = vals['village']
            customer.customer_rank = 1 
        for key in attributes:
            if key == 'email':
               customer.email = attributes[key]
            if key in [key for key in attributes]:
                column_dict = {'partner_id': cust_id}
                existing_attribute = self.env['res.partner.attributes'].sudo().search([('partner_id', '=', cust_id),('name', '=', key)])
                if any(existing_attribute):
                    existing_attribute.unlink()
                column_dict.update({"name": key, "value" : attributes[key]})
                self.env['res.partner.attributes'].sudo().create(column_dict)
