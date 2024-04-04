from collections import defaultdict
from contextlib import ExitStack, contextmanager

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    order_id = fields.Many2one('sale.order',string="Sale ID")
    
    discount_type = fields.Selection([('none', 'No Discount'),
                                      ('fixed', 'Fixed'),
                                      ('percentage', 'Percentage')],
                                     string="Discount Method",
                                     default='none')
    discount = fields.Monetary(string="Discount")
    discount_percentage = fields.Float(string="Discount Percentage")
    disc_acc_id = fields.Many2one('account.account',string="Discount Account Head" ,domain=[('account_type', '=', 'income_other')])
    round_off_amount = fields.Monetary(string="Round Off Amount")

    @contextmanager
    def _check_balanced(self, container):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        with self._disable_recursion(container, 'check_move_validity', default=True, target=False) as disabled:
            yield
            if disabled:
                return
        unbalanced_moves = self._get_unbalanced_moves(container)
    @api.onchange('invoice_line_ids')
    def onchange_invoice_lines(self):
        amount_total = self.amount_untaxed + self.amount_tax
        if self.discount_type == 'fixed':
            self.discount_percentage = (self.discount / amount_total) * 100
        elif self.discount_type == 'percentage':
            self.discount = amount_total * self.discount_percentage / 100

    @api.onchange('discount', 'discount_percentage', 'discount_type')
    def onchange_discount(self):
        amount_total = self.amount_untaxed + self.amount_tax
        if amount_total > 0.00:
            if self.discount_type == 'none':
                self.discount_percentage = 0
                self.discount = 0
                self.disc_acc_id = False
            if self.discount_type == 'percentage':
                self.discount = 0
            if self.discount_type == 'fixed':
                self.discount_percentage = 0            
            if self.discount_percentage:
                self.discount = amount_total * self.discount_percentage / 100
        else:
            pass


    
    def button_dummy(self):
        return True
    
    
    
    
    def action_post(self):
        
        for inv in self: 
            
            find_val = (inv.amount_total - inv.discount ) + inv.round_off_amount
            
            differnece_vals = inv.amount_total - find_val
            
                      
            for move_line in inv.line_ids:
                update = False
                if move_line.display_type =='payment_term':
                    move_line.debit = move_line.debit - differnece_vals

                    
        
        moves_with_payments = self.filtered('payment_id')
        other_moves = self - moves_with_payments
        if moves_with_payments:
            moves_with_payments.payment_id.action_post()
        if other_moves:
            other_moves._post(soft=False)
        return False
    
class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    def invoice_search(self):
        """ Using ref find the invoice obj """
        return self.env['account.move'].search([('id', '=', self.reconciled_invoice_ids.id),('move_type', '=', 'out_invoice')], limit=1)
    
    def total_receivable(self):
        receivable = 0.0
        if self.partner_id:
            self._cr.execute("""select sum(amount_residual) from account_move where 
                          amount_residual > 0 and partner_id = %s
                          """, (self.partner_id.id,))
            outstaning_value = self._cr.fetchall()
            if outstaning_value[0][0] != None: 
                receivable = outstaning_value[0][0]
            else:
                receivable = 0.00                
        return receivable
    
    def generate_report_action(self):
        return self.env.ref("bahmni_account.account_summarized_invoices_payment").report_action(self)
