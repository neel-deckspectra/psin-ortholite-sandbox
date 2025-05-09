# -*- coding: utf-8 -*-

import base64
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import time
from datetime import datetime, timedelta, date
import calendar
import pdb
import datetime
from datetime import date
from datetime import timedelta, datetime
from num2words import num2words


class AccountPayment(models.Model):
    _inherit = 'account.payment'   

    pdc_ids_count = fields.Integer(string='PDC Cheque Count',default=0,compute='_compute_pdc_cheques_payment')
    pdc_cheque_ids = fields.Many2many('post.dated.cheques', compute='_compute_pdc_cheques_payment', string='PDC Cheque(s)', copy=False)
    invoice_reference = fields.Char(string='Invoice Reference')

    def action_open_pdc_cheques_payments(self):
        action = self.env.ref('appscomp_pdc.action_account_pdc_payments_all')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        pdc_cheque_ids = sum([item.pdc_cheque_ids.ids for item in self], [])
        if len(pdc_cheque_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pdc_cheque_ids)) + "])]"
        elif len(pdc_cheque_ids) == 1:
            res = self.env.ref('appscomp_pdc.view_pdc_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pdc_cheque_ids and pdc_cheque_ids[0] or False
        return result

    def _compute_pdc_cheques_payment(self):
        for item in self:
            domain=[('payment_id','=',self.id)]
            pdc_cheque_ids = self.env['post.dated.cheques'].search(domain)
            item.pdc_cheque_ids = pdc_cheque_ids
            item.pdc_ids_count = len(pdc_cheque_ids)