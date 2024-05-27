from odoo import models, fields, api
import psycopg2
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class DbDetails(models.Model):
    _name = 'db.details'
    _description = "DB Details"
    _rec_name = "db_ip"

    # Basic Info
       
    db_ip = fields.Char('DB Host IP', size=25)
    db_name = fields.Char('Database Name', size=50)
    db_uname = fields.Char('DB Username', size=50)
    db_pwd = fields.Char('DB Password', size=50)
    db_port = fields.Char('DB Port', size=10)
    active = fields.Boolean('Active', default=True)
    
    cus_start_id = fields.Integer('Start ID', default=1)
    cus_end_id = fields.Integer('End ID', default=10000)
    
    sup_start_id = fields.Integer('Start ID', default=1)
    sup_end_id = fields.Integer('End ID', default=1000000)
    
    @api.model_create_multi
    def create(self, vals):
        if self.search_count([]) >= 1:
            raise ValidationError("Only one record is allowed in this model.")
        return super(DbDetails, self).create(vals)
        
        
    def test_connection(self):        
        
        try:
            conn = psycopg2.connect(
                dbname= (self.db_name),
                user= (self.db_uname),
                password= (self.db_pwd),
                host= (self.db_ip),
                port= (self.db_port)
            )
            raise UserError(('DB Connection successful!'))
        except Exception as e:
            raise ValidationError(f"Connection Status: {e}")
        
    def uom_cate_creation(self):
        self.env['odoo10_data_import'].uom_category_data_feed()
        
    def uom_creation(self):
        self.env['odoo10_data_import'].uom_data_feed()
        
    def product_cate_creation(self):
        self.env['odoo10_data_import'].product_category_data_feed()
        
    def product_creation(self):
        self.env['odoo10_data_import'].product_data_feed()
        self.env['odoo10_data_import'].product_update_feed()    
   
        
    def supplier_creation(self):
        self.env['odoo10_data_import'].supplier_data_feed(self.sup_start_id,self.sup_end_id)
        
    def customer_creation(self):
        self.env['odoo10_data_import'].customer_data_feed(self.cus_start_id,self.cus_end_id)
       
