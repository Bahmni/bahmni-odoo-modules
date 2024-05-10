from collections import defaultdict
from contextlib import ExitStack, contextmanager

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'
    order_id = fields.Many2one('sale.order', string="Sale ID")

    discount_type = fields.Selection([('none', 'No Discount'),
                                      ('fixed', 'Fixed'),
                                      ('percentage', 'Percentage')],
                                     string="Discount Method",
                                     default='none')
    discount = fields.Monetary(string="Discount")
    discount_percentage = fields.Float(string="Discount Percentage")
    disc_acc_id = fields.Many2one('account.account', string="Discount Account Head",
                                  domain=[('account_type', '=', 'income_other')])
    round_off_amount = fields.Monetary(string="Round Off Amount")
    invoice_total = fields.Monetary(
        string='Invoice Total',
        compute='_compute_invoice_total', readonly=True
    )

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
            final_invoice_value = (inv.amount_total - inv.discount) + inv.round_off_amount
            for move_line in inv.line_ids:
                if move_line.display_type == 'payment_term':
                    if inv.move_type == 'out_invoice':
                        move_line.debit = final_invoice_value
                    if inv.move_type == 'out_refund':
                        move_line.credit = final_invoice_value
        return super(AccountInvoice, self).action_post()

    @api.depends('discount', 'discount_percentage', 'amount_total', 'round_off_amount')
    def _compute_invoice_total(self):
        for invoice in self:
            invoice.invoice_total = (invoice.amount_total - invoice.discount) + invoice.round_off_amount

