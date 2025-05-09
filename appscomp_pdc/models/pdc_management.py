# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.http import request
from odoo import http
import datetime
from collections import defaultdict
import pdb
from num2words import num2words


class PDCAccountJournal(models.Model):
    _inherit = "account.journal"

    default_pdc_account_id = fields.Many2one('account.account', string='Default PDC Account',
                                             domain=[('deprecated', '=', False)],
                                             help="It acts as a default account for PDC cheque",
                                             ondelete='restrict')


class AccountMove(models.Model):
    _inherit = 'account.move'

    pdc_bool = fields.Boolean(string='Is PDC')
    pdc_count = fields.Integer(string='PDC Count', compute='_compute_pdc_count')

    # COMPUTE FUNCTION FOR PDC COUNT
    def _compute_pdc_count(self):
        self.pdc_count = self.env['post.dated.cheques'].sudo().search_count(
            [('invoice_reference', '=', self.name)])

    # FUNCTION TO VIEW PDC FORM DETAILS THROUGH SMART BUTTON
    def get_toll_entry_details_count(self):
        self.sudo().ensure_one()
        form_view = self.sudo().env.ref('appscomp_pdc.view_pdc_form')
        tree_view = self.sudo().env.ref('appscomp_pdc.view_pdc_tree')
        return {
            'name': _('PDC Details'),
            'res_model': 'post.dated.cheques',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('invoice_reference', '=', self.name)],
        }

    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_invoice_reference': self.name,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class PostDatedCheque(models.Model):
    _name = "post.dated.cheques"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "PDC Post Dated Cheque"
    _order = "payment_date desc, name desc"

    name = fields.Char(string='Name', required=True, readonly=True, default=lambda self: _('New'), copy=False)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')], tracking=True, readonly=True,
                                    states={'draft': [('readonly', False)]})
    payment_reference = fields.Char(copy=False, readonly=True,
                                    help="Reference of the document used to issue this payment. Eg. cheque number, "
                                         "file name, etc.")
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, readonly=True,
                                 states={'draft': [('readonly', False)], 'registered': [('readonly', False)]},
                                 tracking=True,
                                 domain="[('type', 'in', ('bank', 'cash'))]")
    payment_type = fields.Selection(
        [('outbound', 'Send Money'), ('inbound', 'Receive Money'), ('transfer', 'Internal Transfer')],
        string='Payment Type', required=True, readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]},
                                 domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    amount = fields.Monetary(string='Amount', required=True, readonly=True, states={'draft': [('readonly', False)]},
                             tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env.company.currency_id)
    bank_reference = fields.Char('Bank Reference', copy=False)
    cheque_reference = fields.Char('Cheque Reference', copy=False)
    effective_date = fields.Date('Effective Date', help='Effective date of PDC', copy=False, default=False,
                                 tracking=True)
    deposit_date = fields.Date('Deposit Date', help='Deposited date of PDC', copy=False, default=False, tracking=True)
    communication = fields.Char(string='Memo', readonly=True, states={'draft': [('readonly', False)]})
    payment_date = fields.Date(string='Date', required=True, readonly=True,
                               states={'draft': [('readonly', False)]}, copy=False, tracking=True)
    payment_id = fields.Many2one('account.payment', string='Payment', tracking=True, readonly=True,
                                 states={'draft': [('readonly', False)]})
    cheque_clear_id = fields.Many2one('account.move', string='Clearance Entry', readonly=True)
    clearance_date = fields.Date(string='Clearance Date', readonly=False, tracking=True)
    unregister_pdc_id = fields.Many2one('account.move', string='Reverse Entry', readonly=True)
    bounce_date = fields.Date(string='Bounce Date', readonly=False, tracking=True)
    return_date = fields.Date(string='Return Date', readonly=False, tracking=True)
    cancel_date = fields.Date(string='Cancel Date', readonly=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('registered', 'Registered'),
        ('deposited', 'Deposited'),
        ('done', 'Cash Received'),
        ('bounced', 'Bounced'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
        ('completed', 'PDC Done')
    ], readonly=True, default='draft',
        copy=False,
        string="Status", tracking=True)
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    active = fields.Boolean('Active', default=True)
    amounts = fields.Float('Amounts')
    check_amount_in_words = fields.Char(string='Amount In Words')
    more_reference = fields.Many2one('account.move', string='More Reference')
    invoice_reference = fields.Char(string='Invoice Reference')

    def _compute_amount2words(self):
        amounts = 0.00
        for rec in self:
            rec.amount_words = str.title(num2words(rec.amount)) + ' ' + 'QR'
            self.amounts = self.amount

    def unreconcile_payment(self):
        self.payment_id.action_draft()
        return True

    def button_cheque_registered(self):
        return self.write({'state': 'registered'})

    def button_cheque_unclear(self):
        if self.cheque_clear_id:
            self.cheque_clear_id.button_draft()
        return self.write({'state': 'deposited', 'clearance_date': ''})

    def button_cheque_completed(self):
        if self.cheque_clear_id:
            # self.cheque_clear_id.button_draft()
            return self.write({'state': 'completed', 'clearance_date': ''})

    def button_cheque_not_bounced(self):
        if self.unregister_pdc_id:
            self.unregister_pdc_id.button_draft()
        return self.write({'state': 'deposited', 'bounce_date': ''})

    def button_cheque_not_returned(self):
        if self.unregister_pdc_id:
            self.unregister_pdc_id.button_draft()
        return self.write({'state': 'deposited', 'return_date': ''})

    def button_cheque_not_cancelled(self):
        if self.unregister_pdc_id:
            self.unregister_pdc_id.button_draft()
        return self.write({'state': 'deposited', 'cancel_date': ''})

    def button_cheque_cancel(self):
        # for record in self:
        #     account_move_obj = record.journal_id
        #     account_move = self.env['account.move']
        #     if record.payment_type == 'inbound':
        #         bank_debit_ledger_id = record.journal_id.default_account_id
        #         customer_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
        #             'appscomp_pdc.customer_accounts_id')
        #         vendor_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
        #             'appscomp_pdc.vendor_accounts_id')
        #         customer_ledger_id = self.env['account.account']. \
        #             sudo().search([('id', '=', customer_accounts_id)], limit=1)
        #         vendor_ledger_id = self.env['account.account']. \
        #             sudo().search([('id', '=', vendor_accounts_id)], limit=1)
        #         pdc_credit_ledger_id = customer_ledger_id
        #         destination_account_id = pdc_credit_ledger_id
        #     elif record.payment_type == 'outbound':
        #         bank_credit_ledger_id = record.journal_id.suspense_account_id
        #         pdc_debit_ledger_id = vendor_ledger_id
        #         destination_account_id = pdc_debit_ledger_id
        #     move = {
        #         'journal_id': account_move_obj.id,
        #         'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #         'ref': record.name,
        #     }
        #     line_ids = []
        #     if record.name and record.bank_reference and record.cheque_reference:
        #         name = 'Cancelled : ' + record.name + ' : ' + record.bank_reference + ' ' + record.cheque_reference
        #     elif record.name and record.bank_reference and not record.cheque_reference:
        #         name = 'Cancelled : ' + record.name + ' : ' + record.bank_reference
        #     elif record.name and record.cheque_reference and not record.bank_reference:
        #         name = 'Cancelled : ' + record.name + ' : ' + record.cheque_reference
        #     if record.payment_type == 'inbound':
        #         domain = [('payment_id', '=', self.payment_id.id)]
        #         move_line_ids = self.env['account.move.line'].search(domain)
        #         for move_line in move_line_ids:
        #             if move_line.account_internal_type == 'liquidity':
        #                 credit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': 0.0,
        #                     'credit': move_line.debit,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(credit_line)
        #             else:
        #                 debit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': move_line.credit,
        #                     'credit': 0.0,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(debit_line)
        #                 destination_account_id = move_line.account_id
        #     elif record.payment_type == 'outbound':
        #         domain = [('payment_id', '=', self.payment_id.id)]
        #         move_line_ids = self.env['account.move.line'].search(domain)
        #         for move_line in move_line_ids:
        #             if move_line.account_internal_type == 'liquidity':
        #                 debit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': move_line.credit,
        #                     'credit': 0.0,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(debit_line)
        #             else:
        #                 credit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': 0.0,
        #                     'credit': move_line.debit,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(credit_line)
        #                 destination_account_id = move_line.account_id
        #     move.update({'line_ids': line_ids})
        #     if record.unregister_pdc_id:
        #         record.unregister_pdc_id.line_ids.unlink()
        #         move_id = record.unregister_pdc_id
        #         move_id.line_ids = line_ids
        #     else:
        #         move_id = account_move.sudo().create(move)
        #     move_id.sudo().post()
        # record.payment_id.move_line_ids.remove_move_reconcile()
        # (record.payment_id.move_line_ids + move_id.line_ids) \
        #     .filtered(lambda line: not line.reconciled and line.account_id == destination_account_id) \
        #     .reconcile()
        self.write({
            'state': 'cancelled',
            # 'unregister_pdc_id': move_id.id,
            'cancel_date': fields.datetime.now().strftime("%Y-%m-%d"),
        })
        return True

    def cron_customer_pdc_follow_up(self, datetime=None):
        service_proposal = self.env['post.dated.cheques'].sudo(). \
            search([('state', 'in', ['draft', 'registered'])])
        accountant_users = ",".join(self.env.ref("account.group_account_user").users.mapped('partner_id.email'))
        for order in service_proposal:
            ctx = self.env.context.copy()
            current_user = self.env.user.name
            current_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            current_url += '/web#view_type=form&model=post.dated.cheques&id=%d' % (order.id)
            cc = ''
            ctx = self.env.context.copy()
            ctx.update({
                'name': order.name,
                'url': current_url,
                'email_cc': order.partner_id.email,
                'email_to': accountant_users,
                'sale_amount': order.amount,
                'effective_date': order.effective_date,
                'partner_id': order.partner_id.name,
                'company_website': order.company_id.website,
                'company_name': order.company_id.name,
                'company_email': order.company_id.email,
                'company_phone': order.company_id.phone,
            })
            import datetime
            datetime_check = (timedelta(hours=00, minutes=00, days=2))
            datetime_after = (timedelta(hours=00, minutes=00, days=1))
            if order.effective_date:
                ref_date1 = order.effective_date
                due_date = date.today()
                import datetime
                cur_date = date.today()
                d11 = str(ref_date1)
                dt21 = datetime.datetime.strptime(d11, '%Y-%m-%d')
                date1 = dt21.strftime("%d/%m/%Y")
                d22 = str(cur_date)
                dt22 = datetime.datetime.strptime(d22, '%Y-%m-%d')
                invoice_due_date = dt22.strftime("%d/%m/%Y")
                due_day = 0
                due_day = (due_date - ref_date1).days
                if order.payment_type == 'inbound':
                    if ref_date1 == cur_date:
                        # if due_day <= datetime_check:
                        template = \
                            self.sudo().env.ref(
                                'appscomp_pdc.email_template_customer_pdc_due_schedule_follow_ups',
                                False)
                        template.with_context(ctx).sudo().send_mail(order.id, force_send=True)
                if order.payment_type == 'outbound':
                    if ref_date1 == cur_date:
                        # if due_day <= datetime_check:
                        template = \
                            self.sudo().env.ref(
                                'appscomp_pdc.email_template_supplier_pdc_due_schedule_follow_ups',
                                False)
                        template.with_context(ctx).sudo().send_mail(order.id, force_send=True)

    # def button_cheque_bounced(self):
    #     for record in self:
    #         account_move_obj = record.journal_id
    #         account_move = self.env['account.move']
    #         customer_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
    #             'appscomp_pdc.customer_accounts_id')
    #         vendor_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
    #             'appscomp_pdc.vendor_accounts_id')
    #         customer_ledger_id = self.env['account.account'].\
    #             sudo().search([('id', '=', customer_accounts_id)], limit=1)
    #         vendor_ledger_id = self.env['account.account'].\
    #             sudo().search([('id', '=', vendor_accounts_id)], limit=1)
    #         if record.payment_type == 'inbound':
    #             bank_debit_ledger_id = record.journal_id.default_account_id
    #             pdc_credit_ledger_id = customer_ledger_id
    #             destination_account_id=pdc_credit_ledger_id
    #         elif record.payment_type == 'outbound':
    #             bank_credit_ledger_id = record.journal_id.suspense_account_id
    #             pdc_debit_ledger_id = vendor_ledger_id
    #             destination_account_id=pdc_debit_ledger_id
    #         move = {
    #             'journal_id': account_move_obj.id,
    #             'date': fields.datetime.now().strftime("%Y-%m-%d"),
    #             'ref': record.name,
    #         }
    #         line_ids = []
    #         if record.name and record.bank_reference and record.cheque_reference:
    #             name = 'Bounced : ' + record.name + ' : ' + record.bank_reference + ' ' + record.cheque_reference
    #         elif record.name and record.bank_reference and not record.cheque_reference:
    #             name = 'Bounced : ' + record.name + ' : ' + record.bank_reference
    #         elif record.name and record.cheque_reference and not record.bank_reference:
    #             name = 'Bounced : ' + record.name + ' : ' + record.cheque_reference
    #         if record.payment_type == 'inbound':
    #             domain = [('payment_id', '=', self.payment_id.id)]
    #             move_line_ids = self.env['account.move.line'].search(domain)
    #             for move_line in move_line_ids:
    #                 if move_line.account_internal_type == 'liquidity':
    #                     credit_line = (0, 0, {
    #                         'name': name,
    #                         'partner_id': record.payment_id.partner_id.id,
    #                         'account_id': move_line.account_id.id,
    #                         'journal_id': account_move_obj.id,
    #                         'date': fields.datetime.now().strftime("%Y-%m-%d"),
    #                         'debit': 0.0,
    #                         'credit': move_line.debit,
    #                         'tax_line_id': False,
    #                     })
    #                     line_ids.append(credit_line)
    #                 else:
    #                     debit_line = (0, 0, {
    #                         'name': name,
    #                         'partner_id': record.payment_id.partner_id.id,
    #                         'account_id': move_line.account_id.id,
    #                         'journal_id': account_move_obj.id,
    #                         'date': fields.datetime.now().strftime("%Y-%m-%d"),
    #                         'debit': move_line.credit,
    #                         'credit': 0.0,
    #                         'tax_line_id': False,
    #                     })
    #                     line_ids.append(debit_line)
    #                     destination_account_id = move_line.account_id
    #         elif record.payment_type == 'outbound':
    #             domain = [('payment_id', '=', self.payment_id.id)]
    #             move_line_ids = self.env['account.move.line'].search(domain)
    #             for move_line in move_line_ids:
    #                 if move_line.account_internal_type == 'liquidity':
    #                     debit_line = (0, 0, {
    #                         'name': name,
    #                         'partner_id': record.payment_id.partner_id.id,
    #                         'account_id': move_line.account_id.id,
    #                         'journal_id': account_move_obj.id,
    #                         'date': fields.datetime.now().strftime("%Y-%m-%d"),
    #                         'debit': move_line.credit,
    #                         'credit': 0.0,
    #                         'tax_line_id': False,
    #                     })
    #                     line_ids.append(debit_line)
    #                 else:
    #                     credit_line = (0, 0, {
    #                         'name': name,
    #                         'partner_id': record.payment_id.partner_id.id,
    #                         'account_id': move_line.account_id.id,
    #                         'journal_id': account_move_obj.id,
    #                         'date': fields.datetime.now().strftime("%Y-%m-%d"),
    #                         'debit': 0.0,
    #                         'credit': move_line.debit,
    #                         'tax_line_id': False,
    #                     })
    #                     line_ids.append(credit_line)
    #                     destination_account_id = move_line.account_id
    #         move.update({'line_ids': line_ids})
    #         if record.unregister_pdc_id:
    #             record.unregister_pdc_id.line_ids.unlink()
    #             move_id = record.unregister_pdc_id
    #             move_id.line_ids = line_ids
    #         else:
    #             move_id = account_move.sudo().create(move)
    #         move_id.sudo().post()
    #     record.payment_id.move_line_ids.remove_move_reconcile()
    #     (record.payment_id.move_line_ids + move_id.line_ids) \
    #         .filtered(lambda line: not line.reconciled and line.account_id == destination_account_id) \
    #         .reconcile()
    #     self.write({
    #         'state': 'bounced',
    #         'unregister_pdc_id': move_id.id,
    #         'bounce_date': fields.datetime.now().strftime("%Y-%m-%d"),
    #     })
    #     return True

    def button_cheque_bounced(self):
        # for record in self:
        #     account_move_obj = record.journal_id
        #     account_move = self.env['account.move']
        #     customer_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
        #         'appscomp_pdc.customer_accounts_id')
        #     vendor_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
        #         'appscomp_pdc.vendor_accounts_id')
        #     customer_ledger_id = self.env['account.account']. \
        #         sudo().search([('id', '=', customer_accounts_id)], limit=1)
        #     vendor_ledger_id = self.env['account.account']. \
        #         sudo().search([('id', '=', vendor_accounts_id)], limit=1)
        #     if record.payment_type == 'inbound':
        #         bank_debit_ledger_id = record.journal_id.default_account_id
        #         pdc_credit_ledger_id = customer_ledger_id
        #         destination_account_id = pdc_credit_ledger_id
        #     elif record.payment_type == 'outbound':
        #         bank_credit_ledger_id = record.journal_id.suspense_account_id
        #         pdc_debit_ledger_id = vendor_ledger_id
        #         destination_account_id = pdc_debit_ledger_id
        #     move = {
        #         'journal_id': account_move_obj.id,
        #         'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #         'ref': record.name,
        #     }
        #     line_ids = []
        #     if record.name and record.bank_reference and record.cheque_reference:
        #         name = 'Bounced : ' + record.name + ' : ' + record.bank_reference + ' ' + record.cheque_reference
        #     elif record.name and record.bank_reference and not record.cheque_reference:
        #         name = 'Bounced : ' + record.name + ' : ' + record.bank_reference
        #     elif record.name and record.cheque_reference and not record.bank_reference:
        #         name = 'Bounced : ' + record.name + ' : ' + record.cheque_reference
        #     if record.payment_type == 'inbound':
        #         domain = [('payment_id', '=', self.payment_id.id)]
        #         move_line_ids = self.env['account.move.line'].search(domain)
        #         for move_line in move_line_ids:
        #             if move_line.account_internal_type == 'liquidity':
        #                 credit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': 0.0,
        #                     'credit': move_line.debit,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(credit_line)
        #             else:
        #                 debit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': move_line.credit,
        #                     'credit': 0.0,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(debit_line)
        #                 destination_account_id = move_line.account_id
        #     elif record.payment_type == 'outbound':
        #         domain = [('payment_id', '=', self.payment_id.id)]
        #         move_line_ids = self.env['account.move.line'].sudo().search(domain)
        #         for move_line in move_line_ids:
        #             if move_line.account_internal_type == 'liquidity':
        #                 debit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': move_line.credit,
        #                     'credit': 0.0,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(debit_line)
        #             else:
        #                 credit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': 0.0,
        #                     'credit': move_line.debit,
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(credit_line)
        #                 destination_account_id = move_line.account_id
        #     move.update({'line_ids': line_ids})
        #     if record.unregister_pdc_id:
        #         record.unregister_pdc_id.line_ids.unlink()
        #         move_id = record.unregister_pdc_id
        #         move_id.line_ids = line_ids
        #     else:
        #         move_id = account_move.sudo().create(move)
        #     move_id.sudo().post()
        # record.payment_id.move_line_ids.remove_move_reconcile()
        # (record.payment_id.move_line_ids + move_id.line_ids) \
        #     .filtered(lambda line: not line.reconciled and line.account_id == destination_account_id) \
        #     .reconcile()
        self.write({
            'state': 'bounced',
            # 'unregister_pdc_id': move_id.id,
            'bounce_date': fields.datetime.now().strftime("%Y-%m-%d"),
        })
        return True

    def button_cheque_returned(self):
        # for record in self:
        #     account_move_obj = record.journal_id
        #     account_move = self.env['account.move']
        #     customer_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
        #         'appscomp_pdc.customer_accounts_id')
        #     vendor_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
        #         'appscomp_pdc.vendor_accounts_id')
        #     customer_ledger_id = self.env['account.account'].search([('id', '=', customer_accounts_id)], limit=1)
        #     vendor_ledger_id = self.env['account.account'].search([('id', '=', vendor_accounts_id)], limit=1)
        #     if record.payment_type == 'inbound':
        #         bank_debit_ledger_id = record.journal_id.default_account_id
        #         pdc_credit_ledger_id = customer_ledger_id
        #         # destination_account_id=pdc_credit_ledger_id
        #     elif record.payment_type == 'outbound':
        #         bank_credit_ledger_id = record.journal_id.suspense_account_id
        #         pdc_debit_ledger_id = vendor_ledger_id
        #         # destination_account_id=pdc_debit_ledger_id
        #     move = {
        #         'journal_id': account_move_obj.id,
        #         'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #         'ref': record.name,
        #     }
        #     line_ids = []
        #     if record.name and record.bank_reference and record.cheque_reference:
        #         name = 'Returned : ' + record.name + ' : ' + record.bank_reference + ' ' + record.cheque_reference
        #     elif record.name and record.bank_reference and not record.cheque_reference:
        #         name = 'Returned : ' + record.name + ' : ' + record.bank_reference
        #     elif record.name and record.cheque_reference and not record.bank_reference:
        #         name = 'Returned : ' + record.name + ' : ' + record.cheque_reference
        #     if record.payment_type == 'inbound':
        #         domain = [('payment_id', '=', self.payment_id.id)]
        #         move_line_ids = self.env['account.move.line'].search(domain)
        #         for move_line in move_line_ids:
        #             if move_line.account_internal_type == 'liquidity':
        #                 credit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': 0.0,
        #                     'credit': move_line.debit,
        #                     # 'analytic_account_id': '',
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(credit_line)
        #             else:
        #                 debit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': move_line.credit,
        #                     'credit': 0.0,
        #                     # 'analytic_account_id': '',
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(debit_line)
        #                 destination_account_id = move_line.account_id
        #     elif record.payment_type == 'outbound':
        #         domain = [('payment_id', '=', self.payment_id.id)]
        #         move_line_ids = self.env['account.move.line'].search(domain)
        #         for move_line in move_line_ids:
        #             if move_line.account_internal_type == 'liquidity':
        #                 debit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': move_line.credit,
        #                     'credit': 0.0,
        #                     # 'analytic_account_id': '',
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(debit_line)
        #             else:
        #                 credit_line = (0, 0, {
        #                     'name': name,
        #                     'partner_id': record.payment_id.partner_id.id,
        #                     'account_id': move_line.account_id.id,
        #                     'journal_id': account_move_obj.id,
        #                     'date': fields.datetime.now().strftime("%Y-%m-%d"),
        #                     'debit': 0.0,
        #                     'credit': move_line.debit,
        #                     # 'analytic_account_id': '',
        #                     'tax_line_id': False,
        #                 })
        #                 line_ids.append(credit_line)
        #                 destination_account_id = move_line.account_id
        #     move.update({'line_ids': line_ids})
        #     if record.unregister_pdc_id:
        #         record.unregister_pdc_id.line_ids.unlink()
        #         move_id = record.unregister_pdc_id
        #         move_id.line_ids = line_ids
        #     else:
        #         move_id = account_move.sudo().create(move)
        #     move_id.sudo().post()
        # record.payment_id.move_line_ids.remove_move_reconcile()
        # (record.payment_id.move_line_ids + move_id.line_ids) \
        #     .filtered(lambda line: not line.reconciled and line.account_id == destination_account_id) \
        #     .reconcile()
        self.write({
            'state': 'returned',
            # 'unregister_pdc_id': move_id.id,
            'return_date': fields.datetime.now().strftime("%Y-%m-%d"),
        })
        return True

    def button_cheque_deposited(self):
        import datetime
        effective_date = self.effective_date
        today = datetime.date.today()
        if (effective_date - today).days > 0:
            raise UserError(_("Alert !! You cannot deposit a cheque before effective date."))
        self.write({'state': 'deposited', 'deposit_date': fields.datetime.now().strftime("%Y-%m-%d")})
        return True

    def button_collect_cash(self):
        for record in self:
            final_name = ''
            if not record.deposit_date:
                raise UserError(_('Alert !! You have not entered the deposited date of PDC'))
            account_move_obj = record.journal_id
            account_move = self.env['account.move']
            customer_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
                'appscomp_pdc.customer_accounts_id')
            vendor_accounts_id = self.env['ir.config_parameter'].sudo().get_param(
                'appscomp_pdc.vendor_accounts_id')
            customer_ledger_id = self.env['account.account']. \
                sudo().search([('id', '=', customer_accounts_id)], limit=1)
            vendor_ledger_id = self.env['account.account']. \
                sudo().search([('id', '=', vendor_accounts_id)], limit=1)
            if record.payment_type == 'inbound':
                # bank_debit_ledger_id = record.journal_id.default_account_id
                bank_debit_ledger = self.env['ir.config_parameter']. \
                    sudo().get_param('appscomp_pdc.customer_accounts_id')
                bank_debit_ledger_id = self.env['account.account']. \
                    sudo().search([('id', '=', bank_debit_ledger)])
                pdc_credit_ledger_id = record.company_id.account_journal_payment_credit_account_id
                destination_account_id = pdc_credit_ledger_id
            elif record.payment_type == 'outbound':
                # bank_credit_ledger_id = record.payment_id.journal_id.default_account_id
                bank_credit_ledger = self.env['ir.config_parameter']. \
                    sudo().get_param('appscomp_pdc.vendor_accounts_id')
                bank_credit_ledger_id = self.env['account.account']. \
                    sudo().search([('id', '=', bank_credit_ledger)])
                # pdc_debit_ledger_id = record.payment_id.journal_id.account_journal_payment_credit_account_id
                pdc_debit_ledger_id = record.company_id.account_journal_payment_debit_account_id
                destination_account_id = pdc_debit_ledger_id
            move = {
                'journal_id': account_move_obj.id,
                'date': fields.datetime.now().strftime("%Y-%m-%d"),
                'ref': record.name,
            }
            line_ids = []
            if record.bank_reference and record.cheque_reference:
                final_name = record.name + ' ' + record.bank_reference + ' ' + record.cheque_reference
            if record.cheque_reference and not record.bank_reference:
                final_name = record.name + '  ' + record.cheque_reference
            if record.payment_type == 'inbound':
                debit_line = (0, 0, {
                    'name': final_name,
                    'partner_id': record.payment_id.partner_id.id,
                    'account_id': bank_debit_ledger_id.id,
                    'journal_id': account_move_obj.id,
                    'date': fields.datetime.now().strftime("%Y-%m-%d"),
                    'debit': record.amount,
                    'credit': 0.0,
                    'tax_line_id': False,
                })
                line_ids.append(debit_line)
                credit_line = (0, 0, {
                    'name': final_name,
                    'partner_id': record.payment_id.partner_id.id,
                    'account_id': pdc_credit_ledger_id.id,
                    'journal_id': account_move_obj.id,
                    'date': fields.datetime.now().strftime("%Y-%m-%d"),
                    'debit': 0.0,
                    'credit': record.amount,
                    'tax_line_id': False,
                })
                line_ids.append(credit_line)
            elif record.payment_type == 'outbound':
                debit_line = (0, 0, {
                    'name': final_name,
                    'partner_id': record.payment_id.partner_id.id,
                    'account_id': pdc_debit_ledger_id.id,
                    'journal_id': account_move_obj.id,
                    'date': fields.datetime.now().strftime("%Y-%m-%d"),
                    'debit': record.amount,
                    'credit': 0.0,
                    'tax_line_id': False,
                })
                line_ids.append(debit_line)
                credit_line = (0, 0, {
                    'name': final_name,
                    'partner_id': record.payment_id.partner_id.id,
                    'account_id': bank_credit_ledger_id.id,
                    'journal_id': account_move_obj.id,
                    'date': fields.datetime.now().strftime("%Y-%m-%d"),
                    'debit': 0.0,
                    'credit': record.amount,
                    'tax_line_id': False,
                })
                line_ids.append(credit_line)
            move.update({'line_ids': line_ids})
            if record.cheque_clear_id:
                record.cheque_clear_id.button_draft()
                record.cheque_clear_id.line_ids.unlink()
                move_id = record.cheque_clear_id
                move_id.update({'line_ids': line_ids})
                move_id.sudo().post()
            if not record.cheque_clear_id:
                move_id = account_move.sudo().create(move)
                move_id.sudo().post()
        # (record.move_line_ids + move_id.line_ids) \
        #     .filtered(lambda line: not line.reconciled and line.account_id == destination_account_id) \
        #     .reconcile()
        self.write({
            'state': 'done',
            'cheque_clear_id': move_id.id,
            'clearance_date': fields.datetime.now().strftime("%Y-%m-%d")
        })
        # pdb.set_trace
        advance_pay = self.env['account.payment'].search([('invoice_reference', '=', self.invoice_reference)])
        move_id_rec = self.env['account.move'].search([('name', '=', self.invoice_reference)])
        if advance_pay:
            for aa in advance_pay:
                if aa.state == 'posted':
                    lines = aa.move_id.line_ids.filtered(lambda line: line.credit > 0)
                    lines += move_id_rec.line_ids.filtered(
                        lambda line: line.account_id == lines[0].account_id and not line.reconciled)
                    lines.reconcile()
        return True

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            if values.get('partner_type') == 'customer':
                values['name'] = self.env['ir.sequence'].next_by_code('account.payment.customer.pdc') or _('New')
            else:
                values['name'] = self.env['ir.sequence'].next_by_code('account.payment.supplier.pdc') or _('New')
        res = super(PostDatedCheque, self).create(values)
        res.write({'state': 'registered'})
        return res
