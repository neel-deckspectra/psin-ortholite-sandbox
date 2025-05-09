# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from ast import literal_eval

def get_lock_date(self):
    # Get account lock date.
    is_accounting_lock_day = self.env['ir.config_parameter'].sudo().get_param('ortholite_account_mrp_fields.is_accounting_lock_day')
    if not is_accounting_lock_day:
        return False
    lock_date_allow_user_ids = self.env['ir.config_parameter'].sudo().get_param('ortholite_account_mrp_fields.lock_date_allow_user_ids')
    current_user = str(self.env.user.id)
    if current_user in lock_date_allow_user_ids:
        return False
    lock_day = int(self.env['ir.config_parameter'].sudo().get_param('ortholite_account_mrp_fields.lock_day'))
    current_date = datetime.today()
    # get last date of current month.
    current_month_last_day = calendar.monthrange(current_date.year, current_date.month)[1]
    if current_month_last_day < int(lock_day):
        # update lack day if lack day greater thane current month last day
        lock_day = current_month_last_day
    lock_date = current_date.replace(day=lock_day)
    if current_date.date() <= lock_date.date():
        return (current_date - relativedelta(months=1)).replace(day=1)
    return lock_date.replace(day=1)



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_accounting_lock_day = fields.Boolean(string="Accounting Lock Day", config_parameter='ortholite_account_mrp_fields.is_accounting_lock_day')
    lock_day = fields.Integer('Lock Day', config_parameter='ortholite_account_mrp_fields.lock_day')
    lock_date_allow_user_ids = fields.Many2many('res.users', string="Allow Users")

    def get_values(self):
        res = super(ResConfigSettings, self).get_values() 
        with_user = self.env['ir.config_parameter'].sudo()   
        com_users = with_user.get_param('ortholite_account_mrp_fields.lock_date_allow_user_ids') 
        res.update(lock_date_allow_user_ids=[(6, 0, literal_eval(com_users))] if com_users else False, )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ortholite_account_mrp_fields.lock_date_allow_user_ids', self.lock_date_allow_user_ids.ids)
        return res

    @api.constrains('lock_day')
    def _check_lock_day(self):
        if self.lock_day > 31 or self.lock_day <= 0:
            raise ValidationError(_("Invalid Monthly Locking Day"))


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains('invoice_date')
    def _check_lock_invoice_date(self):
        # Set lock day validation
        lock_date = get_lock_date(self)
        if lock_date:
            for account in self:
                if account.invoice_date and account.invoice_date < lock_date.date() and account.move_type not in ['in_invoice', 'in_refund']:
                    raise ValidationError(_("You are not allowed to create a transaction as the monthly lock date is passed! Contact account admin."))

    @api.constrains('date')
    def _check_lock_date(self):
        # Set lock day validation
        lock_date = get_lock_date(self)
        if lock_date:
            for account in self:
                if account.date and account.date < lock_date.date():
                    raise ValidationError(_("You are not allowed to create a transaction as the monthly lock date is passed! Contact account admin."))



class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.constrains('date')
    def _check_lock_date(self):
        # Set lock day validation
        lock_date = get_lock_date(self)
        if lock_date:
            for payment in self:
                if payment.date and payment.date < lock_date.date():
                    raise ValidationError(_("You are not allowed to create a transaction as the monthly lock date is passed! Contact account admin."))