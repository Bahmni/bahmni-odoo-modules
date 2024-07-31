from datetime import datetime, date
from lxml import etree
from datetime import timedelta
from itertools import groupby
from markupsafe import Markup
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, format_amount, format_date, html_keep_url, is_html_empty
from odoo.tools.sql import create_index

from odoo.addons.payment import utils as payment_utils

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDF
from odoo.exceptions import UserError
from odoo.tools import pickle
import logging
_logger = logging.getLogger(__name__)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total', 'discount', 'chargeable_amount')
    def _compute_amounts(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            amount_total = amount_untaxed + amount_tax

            if order.discount_type == 'percentage':
                tot_discount = amount_total * order.discount_percentage / 100
            else:
                tot_discount = order.discount

            if order.chargeable_amount > 0.0:
                discount = amount_total - order.chargeable_amount
            else:
                discount = tot_discount
            amount_total = amount_total - discount
            round_off_amount = self.env['rounding.off'].round_off_value_to_nearest(amount_total)
            if order.pricelist_id:
                amt_untax = order.pricelist_id.currency_id.round(amount_untaxed)
                amt_tax = order.pricelist_id.currency_id.round(amount_tax)
            else:
                amt_untax = 0.00
                amt_tax = 0.00

            total_receivable = order._total_receivable()


            order.prev_outstanding_balance = total_receivable
            order.total_outstanding_balance = total_receivable + amount_total + round_off_amount


            order.update({
                'amount_untaxed': amt_untax,
                'amount_tax': amt_tax,
                'amount_total': amount_total + round_off_amount,
                'round_off_amount': round_off_amount,
                'discount': tot_discount,

            })


    def button_dummy(self):
        return self._compute_amounts()

    @api.depends('partner_id')
    def _calculate_balance(self):
        for order in self:
            order.prev_outstanding_balance = 0.0
            order.total_outstanding_balance = 0.0
            total_receivable = order._total_receivable()
            if (total_receivable - order.amount_total) < 0:
                prev_outstanding_amt = 0
            else:
                prev_outstanding_amt = total_receivable - order.amount_total
            order.prev_outstanding_balance = prev_outstanding_amt
            order.total_outstanding_balance = total_receivable

    def _total_receivable(self):
        receivable = 0.0
        if self.partner_id:
            self._cr.execute("""select sum(amount_residual_signed) from account_move where 
                           partner_id = %s""", (self.partner_id.id,))
            outstaning_value = self._cr.fetchall()
            if outstaning_value[0][0] != None:
                receivable = outstaning_value[0][0]
            else:
                receivable = 0.00
        return receivable

    def total_discount_heads(self):


        self._cr.execute("""select acc.code,acc.name,sum(sale.discount) from sale_order sale 
                            left join account_account acc on (acc.id = sale.disc_acc_id)
                            where sale.disc_acc_id is not null
                            group by 1,2
                      """)
        total_discount_value = self._cr.fetchall()
        return total_discount_value

    @api.depends('partner_id')
    def _get_partner_details(self):
        for order in self:
            partner = order.partner_id
            order.update({
                'partner_uuid': partner.uuid,
            })


    partner_village = fields.Many2one("village.village", string="Partner Village")
    care_setting = fields.Selection([('ipd', 'IPD'),
                                     ('opd', 'OPD')], string="Care Setting")
    provider_name = fields.Char(string="Provider Name")
    discount_percentage = fields.Float(string="Discount Percentage")
    default_quantity = fields.Integer(string="Default Quantity")
    # above field is used to allow setting quantity as -1 in sale order line, when it is created through bahmni
    discount_type = fields.Selection([('none', 'No Discount'),
                                      ('fixed', 'Fixed'),
                                      ('percentage', 'Percentage')], string="Discount Type",
                                     default='none')
    discount = fields.Monetary(string="Discount")
    disc_acc_id = fields.Many2one('account.account', string="Discount Account Head" ,domain=[('account_type', '=', 'income_other')])
    round_off_amount = fields.Float(string="Round Off Amount")
    prev_outstanding_balance = fields.Monetary(string="Previous Outstanding Balance",
                                               )
    total_outstanding_balance = fields.Monetary(string="Total Outstanding Balance"
                                                )
    chargeable_amount = fields.Float(string="Chargeable Amount")
    amount_round_off = fields.Float(string="Round Off Amount")
    # location to identify from which location order is placed.
    location_id = fields.Many2one('stock.location', string="Location")
    partner_uuid = fields.Char(string='Customer UUID', store=True, readonly=True, compute='_get_partner_details')
    shop_id = fields.Many2one('sale.shop', 'Shop', required=True)


    @api.onchange('order_line')
    def onchange_order_line(self):
        '''Calculate discount amount, when discount is entered in terms of %'''
        amount_total = self.amount_untaxed + self.amount_tax
        if self.discount_type == 'fixed':
            self.discount_percentage = self.discount/amount_total * 100
        elif self.discount_type == 'percentage':
            self.discount = amount_total * self.discount_percentage / 100

    @api.onchange('discount', 'discount_percentage', 'discount_type', 'chargeable_amount')
    def onchange_discount(self):
        amount_total = self.amount_untaxed + self.amount_tax
        if amount_total > 0.00:
            if self.chargeable_amount:
                if self.discount_type == 'none' and self.chargeable_amount:
                    self.discount_type = 'fixed'
                    discount = amount_total - self.chargeable_amount
                    self.discount_percentage = (discount / amount_total) * 100
            else:
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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        '''1. make percentage and discount field readonly, when chargeable amount is allowed to enter'''
        result = super(SaleOrder, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            group_id = self.env.ref("bahmni_sale.group_allow_change_so_charge").id
            doc = etree.XML(result['arch'])
            if group_id in self.env.user.groups_id.ids:
                for node in doc.xpath("//field[@name='discount_percentage']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, result['fields']['discount_percentage'])
                for node in doc.xpath("//field[@name='discount']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, result['fields']['discount'])
                for node in doc.xpath("//field[@name='discount_type']"):
                    node.set('readonly', '1')
                    setup_modifiers(node, result['fields']['discount_type'])
            result['arch'] = etree.tostring(doc)
        return result

    def _create_invoices(self, grouped=False, final=False, date=None):
        """ Create invoice(s) for the given Sales Order(s).

        :param bool grouped: if True, invoices are grouped by SO id.
            If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
        :param bool final: if True, refunds will be generated if necessary
        :param date: unused parameter
        :returns: created invoices
        :rtype: `account.move` recordset
        :raises: UserError if one of the orders has no invoiceable lines.
        """
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                continue

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        Command.create(
                            order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
                        ),
                    )
                    down_payment_section_added = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    Command.create(
                        line._prepare_invoice_line(sequence=invoice_item_sequence)
                    ),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
            raise UserError(self._nothing_to_invoice_error_message())

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            invoice_vals_list = sorted(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ]
            )
            for _grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                ref_invoice_vals.update({
                    'ref': ', '.join(refs)[:2000],
                    'invoice_origin': ', '.join(origins),
                    'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                })
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                'mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
                subtype_id=self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'))
        if bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_sale.is_invoice_automated')):
            for invoice in self.invoice_ids:
                invoice.action_post()
        return moves


    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        amount_total = self.amount_untaxed + self.amount_tax
        if self.discount_percentage:
            tot_discount = amount_total * self.discount_percentage / 100
        else:
            tot_discount = self.discount

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'currency_id': self.pricelist_id.currency_id.id,
            'narration': self.note,
            'invoice_payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'invoice_line_ids': [],
            'invoice_origin': self.name,
            'payment_reference': self.reference,
            'discount_type': self.discount_type,
            'discount_percentage': self.discount_percentage,
            'disc_acc_id': self.disc_acc_id.id,
            'discount': tot_discount,
            'round_off_amount': self.round_off_amount,
            'order_id': self.id,
            'amount_total': self.amount_total,
        }
        return invoice_vals


    #By Pass the Invoice wizard while we press the "Create Invoice" button in sale order afer confirmation.
    #So Once we Confirm the sale order it will create the invoice and ask for the register payment.
    def action_confirm(self):
        for line in self.order_line:
           if line.display_type in ('line_section', 'line_note'):
               continue
           if line.product_uom_qty <=0:
               raise UserError("Quantity for %s is %s. Please update the quantity or remove the product line."%(line.product_id.name,line.product_uom_qty))
           if line.product_id.tracking == 'lot' and not line.lot_id:
               raise UserError("Kindly choose batch no for %s to proceed further."%(line.product_id.name))

           if 1 < self.order_line.search_count([('lot_id', '=', line.lot_id.id),('order_id', '=', self.id)]) and line.lot_id:
              raise UserError("%s Duplicate batch no is not allowed. Kindly change the batch no to proceed further."%(line.lot_id.name))
           if line.product_uom_qty > line.lot_id.product_qty and line.lot_id:
              raise UserError("Insufficient batch(%s) quantity for %s and available quantity is %s"\
                            %(line.lot_id.name, line.product_id.name, line.lot_id.product_qty))
        res = super(SaleOrder, self.with_context(default_immediate_transfer=True)).action_confirm()
        self.validate_delivery()
        for order in self:
            warehouse = order.warehouse_id
            if order.picking_ids and bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_sale.is_delivery_automated')):
                for picking in self.picking_ids:
                    picking.immediate_transfer = True
                    for move in picking.move_ids:
                        move.quantity_done = move.product_uom_qty
                    picking._autoconfirm_picking()
                    picking.action_set_quantities_to_reservation()
                    picking.action_confirm()
                    for move_line in picking.move_ids_without_package:
                        move_line.quantity_done = move_line.product_uom_qty
                    picking._action_done()
                    for mv_line in picking.move_ids.mapped('move_line_ids'):
                        if not mv_line.qty_done and mv_line.reserved_qty or mv_line.reserved_uom_qty:
                            mv_line.qty_done = mv_line.reserved_qty or mv_line.reserved_uom_qty
        if bool(self.env['ir.config_parameter'].sudo().get_param('bahmni_sale.is_invoice_automated')):
            self._create_invoices()
            if self.env.user.has_group('bahmni_sale.group_redirect_to_payments_on_sale_confirm'):
                action = {
                    'name': _('Payments'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.payment',
                    'context': {'create': False,
                                'default_partner_id': self.partner_id.id,
                                'default_payment_type': 'inbound',
                                'default_partner_type': 'customer',
                                'search_default_inbound_filter': 1},
                    'view_mode': 'form',
                }
                return action
        return res


    #This method will be called when validation is happens from the Bahmni side
    def auto_validate_delivery(self):
        super(SaleOrder, self).action_confirm()
        self.validate_delivery()

    def validate_delivery(self):
        if self.env.ref('bahmni_sale.validate_delivery_when_order_confirmed').value == '1':
            allow_negative = self.env.ref('bahmni_sale.allow_negative_stock')
            if self.picking_ids:
                for picking in self.picking_ids:
                    if picking.state in ('waiting','confirmed','partially_available') and allow_negative.value == '1':
                        picking.force_assign()#Force Available
                    found_issue = False
                    if picking.state not in ('waiting','confirmed','partially_available'):
                        for pack in picking.pack_operation_product_ids:
                            if pack.product_id.tracking != 'none':
                                line = self.order_line.filtered(lambda l:l.product_id == pack.product_id)
                                lot_ids = None
                                if line.lot_id:
                                    lot_ids = line.lot_id
                                else:
                                    lot_ids = self._find_batch(pack.product_id,pack.product_qty,pack.location_id,picking)
                                if lot_ids:
                                    #First need to Find the related move_id of this operation
                                    operation_link_obj = self.env['stock.move.operation.link'].search([('operation_id','=',pack.id)],limit=1)
                                    move_obj = operation_link_obj.move_id
                                    #Now we have to update entry to the related table which holds the lot, stock_move and operation entrys
                                    pack_operation_lot = self.env['stock.pack.operation.lot'].search([('operation_id','=',pack.id)],limit=1)
                                    for lot in lot_ids:
                                        pack_operation_lot.write({
                                            'lot_name': lot.name,
                                            'qty': pack.product_qty,
                                            'operation_id': pack.id,
                                            'move_id': move_obj.id,
                                            'lot_id': lot.id,
                                            'cost_price': lot.cost_price,
                                            'sale_price': lot.sale_price,
                                            'mrp': lot.mrp
                                            })
                                    pack.qty_done = pack.product_qty
                                else:
                                    found_issue = True
                            else:
                                pack.qty_done = pack.product_qty
                        if not found_issue:
                            picking.do_new_transfer()#Validate
                    else:
                        message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are not enough stock available for Some product on <a href=# data-oe-model=stock.location data-oe-id=%d>%s</a> Location") % (self.location_id,self.location_id.name)
                        self.message_post(body=message)

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
                self.message_post(body=message)
        else:
            message = ("<b>Auto validation Failed</b> <br/> <b>Reason:</b> There are no Batches/Serial no's available for <a href=# data-oe-model=product.product data-oe-id=%d>%s</a> product") % (product.id,product.name)
            self.message_post(body=message)
            return False

    @api.onchange('shop_id')
    def onchange_shop_id(self):
        self.warehouse_id = self.shop_id.warehouse_id.id
        self.location_id = self.shop_id.location_id.id
        self.payment_term_id = self.shop_id.payment_default_id.id
        if self.shop_id.pricelist_id:
            self.pricelist_id = self.shop_id.pricelist_id.id

    def validate_payment(self):
        for obj in self:
            ctx = {'active_ids': [obj.id]}
            default_vals = self.env['sale.advance.payment.inv'
                                        ].with_context(ctx).default_get(['count', 'deposit_taxes_id',
                                                                         'advance_payment_method', 'product_id',
                                                                         'deposit_account_id'])
            payment_inv_wiz = self.env['sale.advance.payment.inv'].with_context(ctx).create(default_vals)
            payment_inv_wiz.with_context(ctx).create_invoices()
            for inv in obj.invoice_ids:
                inv.action_invoice_open()
                if inv.state == 'paid':
                    continue
                elif inv.amount_total > 0:
                    account_payment_env = self.env['account.payment']
                    fields = account_payment_env.fields_get().keys()
                    default_fields = account_payment_env.with_context({'default_invoice_ids': [(4, inv.id, None)]}).default_get(fields)
                    journal_id = self.env['account.journal'].search([('type', '=', 'cash')],
                                                                    limit=1)
                    default_fields.update({'journal_id': journal_id.id})
                    payment_method_ids = self.env['account.payment.method'
                                                  ].search([('payment_type', '=', default_fields.get('payment_type'))]).ids
                    if default_fields.get('payment_type') == 'inbound':
                        journal_payment_methods = journal_id.inbound_payment_method_ids.ids
                    elif default_fields.get('payment_type') == 'outbound':
                        journal_payment_methods = journal_id.outbound_payment_method_ids.ids
                    common_payment_method = list(set(payment_method_ids).intersection(set(journal_payment_methods)))
                    common_payment_method.sort()
                    default_fields.update({'payment_method_id': common_payment_method[0]})
                    account_payment = account_payment_env.create(default_fields)
                    account_payment.post()
                else:
                    message = "<b>Auto validation Failed</b> <br/> <b>Reason:</b> The Total amount is 0 So, Can't Register Payment."
                    inv.message_post(body=message)

