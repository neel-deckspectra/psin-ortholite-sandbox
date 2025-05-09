# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
import pytz


class AccountMove(models.Model):
    _inherit = "account.move"

    def get_datetime(self):
        user_tz = self.env.user.tz or 'UTC'
        user_time = datetime.now(pytz.timezone(user_tz))
        return user_time.strftime('%d-%m-%Y %H:%M:%S')

    advance_license_number = fields.Char(string="Advance License Number")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    duty_bcd_inr = fields.Float(string="Duty/BCD INR")
    freight = fields.Float(string="Freight")
    insurance = fields.Float(string="Insurance")
    clearingcharge = fields.Float(string="Clearingcharge")
    liner_charges = fields.Float(string="Liner Charges")
    aai_charges = fields.Float(string="AAI Charges")
    cfs_charges = fields.Float(string="CFS Charges")
    inland_transport = fields.Float(string="Inland Transport")
    fine_amt = fields.Float(string="Fine AMT")
    int_charges = fields.Float(string="Int Charges")
