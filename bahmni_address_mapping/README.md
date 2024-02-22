# Bahmni Address Mapping Module
This module specifically deals with the custom address fields that are required for syncing address information from Bahmni Patient to Odoo 16 Customer.

### Customisations introduced by this module:
1. **Address Mapping Configuration**: This module introduces a new model `address.mapping.table` which is used to map the Bahmni address fields to Odoo address fields. This model is used to store the mapping configuration for each address field.
2. **Address Mapping Service**: This serves as a mapper service that maps the Bahmni address fields to Odoo address fields based on the configuration stored in the `address.mapping.table` model. This is invoked from the api_event_worker class when customer creation or updation happens.
3. **Views for address fields**: The customer create view is customised to include the custom address fields that are intorduced into the Customer creation page of Odoo.
4. **Extending res.partner model of Odoo**: The res.partner model of Odoo is extended to include the custom address fields that are introduced by this module.
5. **Hiding default City field**: The default city field of Odoo is hidden from the customer creation page as it is a text field and a new field village with references to higher address fields is introduced by this module.
