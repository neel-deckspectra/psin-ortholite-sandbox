# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    usd_amount = fields.Float("Amount USD", compute="_compute_usd_amount")
    usd_running_balance = fields.Float("Running Balance USD", compute="_compute_usd_running_balance")

    @api.depends('amount', 'currency_id', 'date')
    def _compute_usd_amount(self):
        usd_currency = self.env.ref('base.USD')
        for line in self:
            date = line.date or fields.Date.context_today(line)
            from_currency = line.currency_id or line.journal_id.currency_id or line.company_id.currency_id
            line.usd_amount = from_currency._convert(line.amount, usd_currency, line.company_id, date)

    @api.depends('amount', 'currency_id', 'date')
    def _compute_usd_running_balance(self):
        usd_currency = self.env.ref('base.USD')
        for line in self:
            date = line.date or fields.Date.context_today(line)
            from_currency = line.currency_id or line.journal_id.currency_id or line.company_id.currency_id
            line.usd_running_balance = from_currency._convert(line.running_balance, usd_currency, line.company_id, date)