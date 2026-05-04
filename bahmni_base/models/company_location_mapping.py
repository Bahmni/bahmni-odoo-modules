# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CompanyLocationMapping(models.Model):
    _name = 'company.location.mapping'
    _description = 'Company to Bahmni Location Mapping Configuration'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        ondelete='cascade'
    )
    
    location_uuid = fields.Char(
        string='Bahmni Location UUID2',
        required=True
    )
    
    _sql_constraints = [
        ('unique_company_id', 'UNIQUE(company_id)', 
         'A company can only have one external identifier configuration!'),
        ('unique_location_uuid', 'UNIQUE(location_uuid)', 
         'This external identifier is already assigned to another company!')
    ]
    
    @api.constrains('company_id', 'location_uuid')
    def _check_unique_mapping(self):
        for record in self:
            existing_company = self.search([
                ('company_id', '=', record.company_id.id),
                ('id', '!=', record.id)
            ])
            if existing_company:
                raise ValidationError(
                    f'Company "{record.company_id.name}" already has an external identifier configured.'
                )
            
            existing_identifier = self.search([
                ('location_uuid', '=', record.location_uuid),
                ('id', '!=', record.id)
            ])
            if existing_identifier:
                raise ValidationError(
                    f'External identifier "{record.location_uuid}" is already assigned to company "{existing_identifier.company_id.name}".'
                )
    
    @api.model
    def get_company_by_location_uuid(self, location_uuid):
        config = self.search([('location_uuid', '=', location_uuid)], limit=1)
        return config.company_id if config else False
