from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_auto_reconciliation_applicable = fields.Boolean(compute="_compute_is_auto_reconciliation_applicable")
    current_outstanding = fields.Float(string="Current Outstanding")
    balance_outstanding = fields.Float(string="Balance Outstanding")

    outstanding_invoice_lines = fields.One2many(
        "account.payment.outstanding.invoice.line",
        "payment_id",
        string="Outstanding Invoice Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Matching Outstanding Invoice Lines", )

    credit_invoice_lines = fields.One2many(
        "account.payment.credit.invoice.line",
        "payment_id",
        string="Credit Invoice Lines",
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Matching Credit Invoice Lines", )

    @api.depends('is_internal_transfer')
    def _compute_is_auto_reconciliation_applicable(self):
        for payment in self:
            payment.is_auto_reconciliation_applicable = \
                bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_auto_payment_reconciliation.enabled')) \
                and not self.is_internal_transfer \
                and self.env.context.get('default_partner_type') == 'customer'

    @api.onchange('partner_id')
    def partner_id_onchange(self):
        if self.is_auto_reconciliation_applicable:
            outstanding_vals = []
            self.outstanding_invoice_lines.unlink()
            if self.partner_id:
                self.current_outstanding = self.total_receivable()
                self.balance_outstanding = self.total_receivable()
                outstanding_invoices = self.env["account.move"].search([("partner_id", "=", self.partner_id.id),
                                                                        ("amount_residual", ">", 0.0),
                                                                        ("state", "=", "posted"),
                                                                        ("company_id", "=", self.company_id.id),
                                                                        ("move_type", "=", "out_invoice")
                                                                        ], order="invoice_date_due,id ASC")

                total_credit = self.total_credit()
                for outstanding_invoice in outstanding_invoices:
                    if outstanding_invoice.amount_residual >= total_credit > 0:
                        allocated_amount = total_credit
                        remaining_amt = outstanding_invoice.amount_residual - total_credit
                        selected = True
                        total_credit = 0

                    elif outstanding_invoice.amount_residual < total_credit:
                        total_credit = total_credit - outstanding_invoice.amount_residual
                        allocated_amount = outstanding_invoice.amount_residual
                        remaining_amt = 0
                        selected = True
                    else:
                        allocated_amount = 0
                        selected = False
                        remaining_amt = outstanding_invoice.amount_residual

                    outstanding_vals.append((0, 0, {
                        'invoice_id': outstanding_invoice.id,
                        'partner_id': outstanding_invoice.partner_id.id,
                        'care_setting': outstanding_invoice.order_id.care_setting,
                        'date': outstanding_invoice.invoice_date_due,
                        'invoice_amt': outstanding_invoice.amount_residual,
                        'allocated_amount': allocated_amount,
                        'remaining_amt': remaining_amt,
                        'selected': selected,
                    }))

            credit_vals = []
            self.credit_invoice_lines.unlink()
            if self.partner_id:
                self.current_outstanding = self.total_receivable()
                self.balance_outstanding = self.total_receivable()
                credit_invoices = self.env["account.move"].search([("partner_id", "=", self.partner_id.id),
                                                                   ("state", "=", "posted"),
                                                                   ("company_id", "=", self.company_id.id),
                                                                   '|', ("amount_residual", "<", 0.0),
                                                                   '&', ("amount_residual", ">", 0.0),
                                                                   ("move_type", "=", "out_refund"),
                                                                   ], order="invoice_date_due,id ASC")

                total_outstanding = self.total_outstanding()
                for credit_invoice in credit_invoices:
                    amount_residual = abs(credit_invoice.amount_residual)
                    if amount_residual >= total_outstanding > 0:
                        allocated_amount = total_outstanding
                        remaining_amt = amount_residual - total_outstanding
                        selected = True
                        total_outstanding = 0

                    elif amount_residual < total_outstanding:
                        total_outstanding = total_outstanding - amount_residual
                        allocated_amount = amount_residual
                        remaining_amt = 0
                        selected = True
                    else:
                        allocated_amount = 0
                        selected = False
                        remaining_amt = amount_residual
                    credit_vals.append((0, 0, {
                        'invoice_id': credit_invoice.id,
                        'partner_id': credit_invoice.partner_id.id,
                        'care_setting': credit_invoice.order_id.care_setting,
                        'date': credit_invoice.invoice_date_due,
                        'invoice_amt': amount_residual,
                        'remaining_amt': remaining_amt,
                        'allocated_amount': allocated_amount,
                        'selected': selected,

                    }))
            return {'value': {'outstanding_invoice_lines': outstanding_vals,
                              'credit_invoice_lines': credit_vals}}

    @api.onchange('amount')
    def paid_amount_onchange(self):
        if self.amount < 0:
            raise ValidationError("Payment amount should not be in negative")
        if self.is_auto_reconciliation_applicable:
            self.balance_outstanding = self.total_receivable() - self.amount
            if self.balance_outstanding < 0 and self.amount > 0:
                raise ValidationError("Payment amount should not be greater than current outstanding amount")
            paid_amt = self.amount + self.total_credit()
            for line in self.outstanding_invoice_lines:
                line.remaining_amt = line.invoice_amt
                line.allocated_amount = 0.00
                line.selected = False
                if line.remaining_amt >= paid_amt and paid_amt > 0:
                    line.allocated_amount = paid_amt
                    line.remaining_amt = line.remaining_amt - paid_amt
                    line.selected = True
                    paid_amt = 0
                else:
                    if line.remaining_amt < paid_amt:
                        remaining_bal = 0
                        paid_amt = paid_amt - line.remaining_amt
                        line.allocated_amount = line.remaining_amt
                        line.remaining_amt = remaining_bal
                        line.selected = True

    def action_post(self):
        if self.is_auto_reconciliation_applicable:
            if self.balance_outstanding < 0 and self.amount > 0:
                raise ValidationError("Payment amount should not be greater than current outstanding amount")
            res = super(AccountPayment, self).action_post()
            if len(self.credit_invoice_lines) > 0:
                self.assign_credit_invoices_to_outstanding_invoices()
            unprocessed_outstanding_invoices = self.get_unprocessed_outstanding_invoices()
            if unprocessed_outstanding_invoices and self.amount > 0 and self.payment_type == 'inbound':
                self.assign_payment_to_outstanding_invoices(unprocessed_outstanding_invoices)
        else:
            res = super(AccountPayment, self).action_post()
        return res

    def action_draft(self):
        super(AccountPayment, self).action_draft()
        _logger.info("Default Payment Reset Flow completed. Resetting credit invoice allocations.")
        self.unlink_credit_invoice_associations()

    def cashier_name(self):
        words = self.create_uid.name.split()
        initials = ''.join(word[0].upper() for word in words)
        return initials

    def total_credit(self):
        credit_value = 0.0
        if self.partner_id:
            self._cr.execute("""select sum(ABS(amount_residual)) from account_move where 
                          (amount_residual < 0 or (move_type='out_refund' and amount_residual > 0)) and state='posted' and partner_id = %s
                          """, (self.partner_id.id,))
            result = self._cr.fetchall()
            if result[0][0] is not None:
                credit_value = result[0][0]
            else:
                credit_value = 0.00
        return credit_value

    def total_outstanding(self):
        outstanding = 0.0
        if self.partner_id:
            self._cr.execute("""select sum(amount_residual) from account_move where 
                              amount_residual > 0 and move_type='out_invoice' and state='posted' and partner_id = %s
                              """, (self.partner_id.id,))
            outstanding_value = self._cr.fetchall()
            if outstanding_value[0][0] is not None:
                outstanding = outstanding_value[0][0]
            else:
                outstanding = 0.00
        return outstanding

    def total_receivable(self):
        return self.total_outstanding() - self.total_credit()

    def assign_credit_invoices_to_outstanding_invoices(self):
        for credit_invoice in self.credit_invoice_lines:
            associated_invoices = []
            if credit_invoice.selected:
                payment_term_line_id = credit_invoice.invoice_id.line_ids.filtered(
                    lambda l: l.display_type == 'payment_term')
                for outstanding_invoice in self.get_unprocessed_outstanding_invoices():
                    outstanding_invoice.invoice_id.js_assign_outstanding_line(payment_term_line_id.id)
                    associated_invoices.append(outstanding_invoice.invoice_id.name)
                    if credit_invoice.invoice_id.amount_residual == 0:
                        _logger.info("Credit Invoice %s assigned to : %s" % (credit_invoice.invoice_id.name,
                                                                             ', '.join(associated_invoices)))
                        break

    def get_unprocessed_outstanding_invoices(self):
        return self.outstanding_invoice_lines.filtered(lambda l: l.selected and l.invoice_id.amount_residual > 0)

    def assign_payment_to_outstanding_invoices(self, outstanding_invoices):
        payment_line_entry = self.env["account.move.line"].search([("partner_id", "=", self.partner_id.id),
                                                                   ("payment_id", "=", self.id),
                                                                   ("company_id", "=", self.company_id.id),
                                                                   ("amount_residual", "<", 0.0),
                                                                   ])
        associated_invoices = []
        for outstanding_invoice in outstanding_invoices:
            outstanding_invoice.invoice_id.js_assign_outstanding_line(payment_line_entry.id)
            associated_invoices.append(outstanding_invoice.invoice_id.name)
            if payment_line_entry.amount_residual == 0:
                _logger.info("Payment %s assigned to : %s" % (self.name,
                                                              ', '.join(associated_invoices)))
                break

    def unlink_credit_invoice_associations(self):
        allocated_credit_invoices = self.credit_invoice_lines.filtered(lambda l: l.selected)
        for allocated_credit_invoice in allocated_credit_invoices:
            partial_reconciles, exchange_move_diffs = allocated_credit_invoice.invoice_id._get_reconciled_invoices_partials()
            _logger.info("Reconciles:" + str(partial_reconciles))
            for (partial_reconcile, amount, move_line) in partial_reconciles:
                associated_outstanding_invoice = self.outstanding_invoice_lines.filtered(
                    lambda l: l.selected and l.invoice_id == move_line.move_id)
                if associated_outstanding_invoice:
                    _logger.info("Un reconciling credit invoice %s from %s for amount %s" % (
                        allocated_credit_invoice.invoice_id.name, associated_outstanding_invoice.invoice_id.name,
                        amount))
                    associated_outstanding_invoice.invoice_id.js_remove_outstanding_partial(partial_reconcile.id)

    # Support Functions for Receipt Print
    def generate_report_action(self):
        return self.env.ref("bahmni_auto_payment_reconciliation.account_payment_summary_receipt").report_action(self)

    def get_latest_invoice_for_date(self, invoice_date):
        return self.env['account.move'].search([('move_type', '=', 'out_invoice'),
                                                ('partner_id', '=', self.partner_id.id),
                                                ('invoice_date', '=', invoice_date)],
                                               order="id desc",
                                               limit=1)

    def get_invoice_amount_details_for_print(self):
        invoice = self.get_latest_invoice_for_date(self.move_id.date)
        net_amount = self.current_outstanding
        paid_amount = self.amount
        balance_outstanding = self.balance_outstanding
        previous_balance = self.calculate_previous_balance(invoice)
        new_charges = 0
        discount = 0
        if invoice:
            new_charges = invoice.amount_total + invoice.round_off_amount
            discount = invoice.discount
        return {
            "invoice": invoice,
            "previous_balance": previous_balance,
            "new_charges": new_charges,
            "discount": discount,
            "net_amount": net_amount,
            "paid_amount": paid_amount,
            "balance_outstanding": balance_outstanding
        }

    def calculate_previous_balance(self, invoice):
        if not invoice:
            return self.current_outstanding
        previous_balance = 0
        for line in self.outstanding_invoice_lines.filtered(lambda l: l.invoice_id.id != invoice.id):
            previous_balance += line.invoice_amt
        for line in self.credit_invoice_lines.filtered(lambda l: l.invoice_id.id != invoice.id):
            previous_balance -= line.invoice_amt
        return previous_balance

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


class AccountPaymentOutStandingInvoiceLine(models.Model):
    _name = "account.payment.outstanding.invoice.line"
    _description = "Account Payment Outstanding Invoice Line(s)"

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

    allocated_amount = fields.Float(string="Allocated Amount")
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


class AccountPaymentCreditInvoiceLine(models.Model):
    _name = "account.payment.credit.invoice.line"
    _description = "Account Payment Credit Invoice Line(s)"

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

    allocated_amount = fields.Float(string="Allocated Amount")
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
