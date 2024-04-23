from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero

class AccountPayment(models.Model):
    _inherit = "account.payment"

    prev_outstanding_balance = fields.Float(string="Previous Outstanding")
    balance_outstanding = fields.Float(string="Balance Outstanding")
    
    line_payment_invoice_credit_ids = fields.One2many(
        "account.payment.credit.invoice.line",
        "payment_id",
        string="Invoice Credit Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Use these lines to add matching lines, for example in a credit",)
        
    line_payment_invoice_debit_ids = fields.One2many(
        "account.payment.debit.invoice.line",
        "payment_id",
        string="Invoice Debit Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Use these lines to add matching lines, for example in a credit",)
    
    
    def multi_invoice_search(self):
        """ Using ref find the invoice obj """
        return self.env['account.move'].search([('move_type', '=', 'out_invoice'),('amount_residual', '>', 0),('partner_id', '=', self.partner_id.id)], order = "id desc", limit=1)
    
    def generate_report_action(self):
        return self.env.ref("bahmni_multi_payment.account_summarized_multi_invoices_payment").report_action(self)
        
    def cashier_name(self):        
        words = self.create_uid.name.split()
        initials = ''.join(word[0].upper() for word in words)
        return initials
    
    def total_debits(self):
        debit_balance = 0.0
        if self.partner_id:
            self._cr.execute("""select ABS(sum(amount_residual)) from account_move where 
                          amount_residual < 0 and partner_id = %s
                          """, (self.partner_id.id,))
            debit_value = self._cr.fetchall()
            if debit_value[0][0] != None: 
                debit_balance = debit_value[0][0]
            else:
                debit_balance = 0.00                
        return debit_balance
    
    def action_post(self): 
        total_payable_value = total_invoice_amount = 0       
        for credit_rec in self.line_payment_invoice_credit_ids:
            if credit_rec.selected == True:
                # ~ credit_rec.invoice_id.amount_residual = credit_rec.invoice_id.amount_residual - credit_rec.amount
                # ~ credit_rec.invoice_id.amount_residual_signed = credit_rec.invoice_id.amount_residual - credit_rec.amount
                
                invoice_line_data = self.env["account.move.line"].search([("partner_id", "=",self.partner_id.id),
                ("amount_residual", ">", 0.0),
                ("parent_state", "=", "posted"),
                ("display_type", "=", "payment_term"),
                ("move_id", "=", credit_rec.invoice_id.id),
                ("company_id", "=", self.company_id.id),
                ])
                invoice_line_data.amount_residual = invoice_line_data.amount_residual - credit_rec.amount
                invoice_line_data.amount_residual_currency = invoice_line_data.amount_residual_currency - credit_rec.amount
                                
                if credit_rec.remaining_amt > 0:
                    credit_rec.invoice_id.payment_state = 'partial'
                else:
                    credit_rec.invoice_id.payment_state = 'paid'
                    
            total_payable_value +=  credit_rec.amount
            total_invoice_amount +=  credit_rec.invoice_amt
              
                    
        for debit_rec in self.line_payment_invoice_debit_ids:            
            if total_payable_value > 0:                                                
                if abs(debit_rec.invoice_id.amount_residual) <= total_payable_value:
                    total_payable_value = total_payable_value - abs(debit_rec.invoice_id.amount_residual)                    
                    # ~ debit_rec.invoice_id.amount_residual = 0
                    # ~ debit_rec.invoice_id.amount_residual_signed = 0
                    
                    invoice_line_data = self.env["account.move.line"].search([("partner_id", "=",self.partner_id.id),
                    ("amount_residual", "<", 0.0),
                    ("parent_state", "=", "posted"),
                    ("display_type", "=", "payment_term"),
                    ("move_id", "=", debit_rec.invoice_id.id),
                    ("company_id", "=", self.company_id.id),
                    ])
                    invoice_line_data.amount_residual = 0
                    invoice_line_data.amount_residual_currency = 0
                    
                    debit_rec.invoice_id.payment_state = 'paid'                    
                else:                   
                    # ~ debit_rec.invoice_id.amount_residual = total_payable_value + debit_rec.invoice_id.amount_residual
                    # ~ debit_rec.invoice_id.amount_residual_signed = total_payable_value + debit_rec.invoice_id.amount_residual
                    
                    invoice_line_data = self.env["account.move.line"].search([("partner_id", "=",self.partner_id.id),
                    ("amount_residual", "<", 0.0),
                    ("parent_state", "=", "posted"),
                    ("display_type", "=", "payment_term"),
                    ("move_id", "=", debit_rec.invoice_id.id),
                    ("company_id", "=", self.company_id.id),
                    ])
                    invoice_line_data.amount_residual = total_payable_value + invoice_line_data.amount_residual
                    invoice_line_data.amount_residual_currency = total_payable_value + invoice_line_data.amount_residual_currency
                    
                    debit_rec.invoice_id.payment_state = 'partial'
                         
        
        if self.balance_outstanding < 0 and self.amount > 0:
            raise UserError("Paid amount should not be greather than current outstanding amount")        
        res = super(AccountPayment, self).action_post()
        
        if self.line_payment_invoice_credit_ids:
            invoice_pay_line_data = self.env["account.move.line"].search([("partner_id", "=",self.partner_id.id),
            ("payment_id", "=", self.id),
            ("amount_residual", "<", 0.0),
            ("company_id", "=", self.company_id.id),
            ])
            
            invoice_pay_line_data.amount_residual = 0
            invoice_pay_line_data.amount_residual_currency = 0           
            
            print("invoice_pay_line_data",invoice_pay_line_data)
        
                
        return res    
    
    @api.onchange('amount')
    def paid_amount_onchange(self):
        self.balance_outstanding = (self.total_receivable() - self.total_debits()) - self.amount
        paid_amt = self.amount + self.total_debits()
        for line in self.line_payment_invoice_credit_ids:
            line.remaining_amt = line.invoice_amt
            line.amount = 0.00
            line.selected = False
            if line.remaining_amt >= paid_amt and paid_amt > 0:
                line.amount = paid_amt
                line.remaining_amt = line.remaining_amt - paid_amt
                line.selected = True
                paid_amt = 0
            else:
                if line.remaining_amt <  paid_amt:
                    remaining_bal = 0
                    paid_amt = paid_amt - line.remaining_amt 
                    line.amount = line.remaining_amt
                    line.remaining_amt = remaining_bal
                    line.selected = True
                        
    
    @api.onchange('partner_id')
    def partner_id_onchange(self):
            
        credit_vals = []
        self.line_payment_invoice_credit_ids.unlink()
        if self.partner_id:
            self.prev_outstanding_balance = self.total_receivable() - self.total_debits()
            self.balance_outstanding = self.total_receivable() - self.total_debits()            
            invoice_data = self.env["account.move"].search([("partner_id", "=",self.partner_id.id),
                ("amount_residual", ">", 0.0),
                ("state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ],order="invoice_date_due,id ASC")            
            
            debit_total_value =  self.total_debits() 
            for credit_invoice in invoice_data:
                if credit_invoice.amount_residual >= debit_total_value and debit_total_value > 0:
                    amount = debit_total_value
                    remaining_amt = credit_invoice.amount_residual - debit_total_value
                    selected = True
                    debit_total_value = 0
                
                elif credit_invoice.amount_residual <  debit_total_value:
                    debit_total_value = debit_total_value - credit_invoice.amount_residual
                    amount = credit_invoice.amount_residual
                    remaining_amt = 0
                    selected = True
                else:
                    amount =  0   
                    selected = False  
                    remaining_amt = credit_invoice.amount_residual               
                                     
                credit_vals.append((0, 0, {
                'invoice_id': credit_invoice.id,
                'partner_id': credit_invoice.partner_id.id,
                'care_setting': credit_invoice.order_id.care_setting,
                'date': credit_invoice.invoice_date_due,
                'remaining_amt': remaining_amt,
                'amount': amount,
                'selected': selected,
                'invoice_amt': credit_invoice.amount_residual,                
                }))   
                
        debit_vals = []
        self.line_payment_invoice_debit_ids.unlink()
        if self.partner_id:
            self.prev_outstanding_balance = self.total_receivable() - self.total_debits()
            self.balance_outstanding = self.total_receivable() - self.total_debits()            
            debit_invoice_data = self.env["account.move"].search([("partner_id", "=",self.partner_id.id),
                ("amount_residual", "<", 0.0),
                ("state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ],order="invoice_date_due ASC")
                       
            for debit_invoice in debit_invoice_data:                                     
                debit_vals.append((0, 0, {
                'invoice_id': debit_invoice.id,
                'partner_id': debit_invoice.partner_id.id,
                'care_setting': debit_invoice.order_id.care_setting,
                'date': debit_invoice.invoice_date_due,
                'remaining_amt': abs(debit_invoice.amount_residual),
                'invoice_amt': abs(debit_invoice.amount_residual),
                'amount': abs(debit_invoice.amount_residual),
                'selected': True,
                
                }))  
        return {'value': {'line_payment_invoice_credit_ids': credit_vals,'line_payment_invoice_debit_ids': debit_vals}} 
    
    ## Entry Deletion ##   
    def unlink(self):
        """ unlink """
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    _('Warning!, You can not delete this entry !!'))
            if rec.state == 'draft':
                models.Model.unlink(rec)
        return True

class AccountPaymentCreditInvoiceLine(models.Model):
    _name = "account.payment.credit.invoice.line"  
    _description = "Account Payment Credit Invoice Line"

    payment_id = fields.Many2one(
        "account.payment", string="Payment", required=False, ondelete="cascade")
        
    invoice_id = fields.Many2one(
        "account.move", string="Invoice No.")
    partner_id = fields.Many2one("res.partner", string="Customer", ondelete="restrict")
    
    move_ids = fields.One2many(
        "account.move.line",
        "payment_line_id",
        string="Journal Entries Created",
    ),
    
    amount = fields.Float(string="Amount")
    remaining_amt = fields.Float(string="Remaining Amount")
    invoice_amt = fields.Float(string="Invoice Balance")
    selected = fields.Boolean(string="Selected")    
    date = fields.Date(string='Date')
    care_setting = fields.Selection([('ipd', 'IPD'),
                                     ('opd', 'OPD')], string="Care Setting")
                                     
    def unlink(self):
        """ unlink """
        for rec in self:                    
            models.Model.unlink(rec)
        return True
        
        
class AccountPaymentDebitInvoiceLine(models.Model):
    _name = "account.payment.debit.invoice.line"  
    _description = "Account Payment Debit Invoice Line"

    payment_id = fields.Many2one(
        "account.payment", string="Payment", required=False, ondelete="cascade")
        
    invoice_id = fields.Many2one(
        "account.move", string="Invoice No.")
    partner_id = fields.Many2one("res.partner", string="Customer", ondelete="restrict")
    
    move_ids = fields.One2many(
        "account.move.line",
        "payment_line_id",
        string="Journal Entries Created",
    ),
    
    amount = fields.Float(string="Amount")
    remaining_amt = fields.Float(string="Remaining Amount")
    invoice_amt = fields.Float(string="Invoice Balance")
    selected = fields.Boolean(string="Selected")    
    date = fields.Date(string='Date')
    care_setting = fields.Selection([('ipd', 'IPD'),
                                     ('opd', 'OPD')], string="Care Setting")
                                     
    def unlink(self):
        """ unlink """        
        for rec in self:                      
            models.Model.unlink(rec)
        return True
