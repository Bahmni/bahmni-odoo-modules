from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)
# mapping invoice type to refund type
TYPE2REFUND = {
    'out_invoice': 'out_refund',        # Customer Invoice
    'in_invoice': 'in_refund',          # Vendor Bill
    'out_refund': 'out_invoice',        # Customer Refund
    'in_refund': 'in_invoice',          # Vendor Refund
}

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    discount_type = fields.Selection([('none', 'No Discount'),
                                      ('fixed', 'Fixed'),
                                      ('percentage', 'Percentage')],
                                     string="Discount Method",
                                     default='none')
    discount = fields.Monetary(string="Discount")
    discount_percentage = fields.Float(string="Discount Percentage")
    disc_acc_id = fields.Many2one('account.account',
                                  string="Discount Account Head")
    round_off_amount = fields.Monetary(string="Round Off Amount",
                                       )

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
        if self.discount:
            self.discount_percentage = (self.discount / amount_total) * 100
        if self.discount_percentage:
            self.discount = amount_total * self.discount_percentage / 100

    def _find_batch(self, product, qty, location, picking):
        _logger.info("\n\n***** Product :%s, Quantity :%s Location :%s\n*****",product,qty,location)
        lot_objs = self.env['stock.production.lot'].search([('product_id','=',product.id),('life_date','>=',str(fields.datetime.now()))])
        _logger.info('\n *** Searched Lot Objects:%s \n',lot_objs)
        if any(lot_objs):
            #Sort losts based on the expiry date FEFO(First Expiry First Out)
            lot_objs = list(lot_objs)
            sorted_lot_list = sorted(lot_objs, key=lambda l: l.life_date)
            _logger.info('\n *** Sorted based on FEFO :%s \n',sorted_lot_list)
            done_qty = qty
            res_lot_ids = []
            lot_ids_for_query = tuple([lot.id for lot in sorted_lot_list])
            self._cr.execute("SELECT SUM(qty) FROM stock_quant WHERE lot_id IN %s and location_id=%s",(lot_ids_for_query,location.id,))
            qry_rslt = self._cr.fetchall()
            available_qty = qry_rslt[0] and qry_rslt[0][0] or 0
            if available_qty >= qty:
                for lot_obj in sorted_lot_list:
                    quants = lot_obj.quant_ids.filtered(lambda q: q.location_id == location)
                    for quant in quants:
                        if done_qty >= 0:
                            res_lot_ids.append(lot_obj)
                            done_qty = done_qty - quant.qty
                return res_lot_ids
            else:
                message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are not enough stock available for <a href=# data-oe-model=product.product data-oe-id=%d>%s</a> product on <a href=# data-oe-model=stock.location data-oe-id=%d>%s</a> Location") % (product.id,product.name,location.id,location.name)
                picking.message_post(body=message)
        else:
            message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are no Batches/Serial no's available for <a href=# data-oe-model=product.product data-oe-id=%d>%s</a> product") % (product.id,product.name)
            picking.message_post(body=message)
            return False
    
    def button_dummy(self):
        return True
    
    
    
    
    def action_post(self):
        
        for inv in self: 
            print("inv",inv.discount,inv.round_off_amount,inv.amount_total) 
            
            find_val = (inv.amount_total - inv.discount ) + inv.round_off_amount
            
            print("find_val",find_val)
            differnece_vals = inv.amount_total - find_val
            print("differnece_vals",differnece_vals)
            
                      
            for move_line in inv.line_ids:
                update = False
                print("move_line",move_line.display_type)
                if move_line.display_type =='payment_term':
                    move_line.debit = move_line.debit - differnece_vals

                    
        
        moves_with_payments = self.filtered('payment_id')
        other_moves = self - moves_with_payments
        if moves_with_payments:
            moves_with_payments.payment_id.action_post()
        if other_moves:
            other_moves._post(soft=False)
        return False
    
   

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        """ Prepare the dict of values to create the new refund from the invoice.
            This method may be overridden to implement custom
            refund generation (making sure to call super() to establish
            a clean extension chain).

            :param record invoice: invoice to refund
            :param string date_invoice: refund creation date from the wizard
            :param integer date: force date from the wizard
            :param string description: description of the refund from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the refund
        """
        values = {}
        for field in self._get_refund_copy_fields():
            if invoice._fields[field].type == 'many2one':
                values[field] = invoice[field].id
            else:
                values[field] = invoice[field] or False

        values['invoice_line_ids'] = self._refund_cleanup_lines(invoice.invoice_line_ids)
        tax_lines = invoice.tax_line_ids
        taxes_to_change = {
            line.tax_id.id: line.tax_id.refund_account_id.id
            for line in tax_lines.filtered(lambda l: l.tax_id.refund_account_id != l.tax_id.account_id)
        }
        cleaned_tax_lines = self._refund_cleanup_lines(tax_lines)
        values['tax_line_ids'] = self._refund_tax_lines_account_change(cleaned_tax_lines, taxes_to_change)

        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
        elif invoice['type'] == 'in_invoice':
            journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        else:
            journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        values['journal_id'] = journal.id

        values['type'] = TYPE2REFUND[invoice['type']]
        values['date_invoice'] = date_invoice or fields.Date.context_today(invoice)
        values['state'] = 'draft'
        values['number'] = False
        values['origin'] = invoice.number
        values['payment_term_id'] = False
        values['refund_invoice_id'] = invoice.id
        #=============Customized code starts========= Added Custom discount fields in refund
        values['discount_type'] = invoice.discount_type
        values['discount'] = invoice.discount
        values['discount_percentage'] = invoice.discount_percentage
        values['disc_acc_id'] = invoice.disc_acc_id.id
        #===========Customized code ends=============

        if date:
            values['date'] = date
        if description:
            values['name'] = description
        return values

