from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ApiEventWorker(models.Model):
    _name = 'api.event.worker'
    _auto = False

    @api.model
    def process_event(self, vals):
        '''Method getting triggered from Bahmni side'''
        _logger.debug("API Payload:" + str(vals))
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
            elif category == "create.radiology.test":
                self.env['reference.data.service'].create_or_update_ref_data(vals, 'Radiology')
                return "The rediology test have been successfully created / updated."
            elif category == "create.lab.test":
                self.env['reference.data.service'].create_or_update_ref_data(vals, 'Test')
                return "The lab test have been successfully created / updated."
            elif category == "create.lab.panel":
                self.env['reference.data.service'].create_or_update_ref_data(vals, 'Panel')
                return "The lab panel have been successfully created / updated."
            elif category == "create.service.saleable":
                self.env['reference.data.service'].create_or_update_ref_data(vals, 'Others')
                return "The service saleable have been successfully created / updated."
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
        address_data = vals.get('preferredAddress')
        # get validated address details
        address_details = self.env['address.mapping.service']._map_address_fields(address_data)
        # update address details
        customer_vals.update(address_details)
        _logger.info("Customer vals: %s", customer_vals)
        existing_customer = self.env['res.partner'].search([('ref', '=', patient_ref)])
        if existing_customer:
            existing_customer.write(customer_vals)
            self._create_or_update_person_attributes(existing_customer.id,vals)
        else:
            customer = self.env['res.partner'].create(customer_vals)
            self._create_or_update_person_attributes(customer.id,vals)

    def _get_customer_vals(self, vals):
        res = {}
        res.update({'ref': vals.get('ref'),
                    'name': vals.get('name'),
                    'local_name': vals.get('local_name') if vals.get('local_name') else False,
                    'uuid': vals.get('uuid'),
                    'customer_rank':  1})
        # update other details : for now there is only scope of updating contact.
        if vals.get('primaryContact'):
            res.update({'phone': vals['primaryContact']})
        return res

    def _create_or_update_person_attributes(self, cust_id, vals):
        attributes = vals.get("attributes", "{}")
        address_data = vals.get('preferredAddress')

        if attributes.get('email') and cust_id:
            customer_master = self.env['res.partner'].search([('id', '=', cust_id)])
            if customer_master:
                customer_master.email = attributes['email']



        for key in attributes:
            if key in [key for key in attributes]:
                column_dict = {'partner_id': cust_id}
                existing_attribute = self.env['res.partner.attributes'].search([('partner_id', '=', cust_id),('name', '=', key)])
                if any(existing_attribute):
                    existing_attribute.unlink()
                column_dict.update({"name": key, "value" : attributes[key]})
                self.env['res.partner.attributes'].create(column_dict)
