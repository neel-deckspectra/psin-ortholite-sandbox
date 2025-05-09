# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    brands = fields.Char(string="Brand", related="move_id.brand_ids.name", store=True)

    @api.model
    def _select(self):
        return super()._select() + ", ct.name as brands"

    @api.model
    def _from(self):
        return super()._from() + "LEFT JOIN account_move_crm_tag_rel amctr ON amctr.account_move_id = move.id LEFT JOIN crm_tag ct ON ct.id = amctr.crm_tag_id"
