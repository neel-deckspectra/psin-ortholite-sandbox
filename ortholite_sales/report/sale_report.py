# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'

    tag = fields.Char(string="Brand", readonly=True)

    def _select_additional_fields(self):
        # Select tag data
        res = super()._select_additional_fields()
        lang = self.env.user.lang or get_lang(self.env).code
        res['tag'] = f"ct.name->>'{lang}'"
        return res

    def _from_sale(self):
        res = super()._from_sale()
        # Join sale_order_tag_rel table to fetch tag_ids
        res += """
            LEFT JOIN sale_order_tag_rel so_tag ON so_tag.order_id = s.id
            LEFT JOIN crm_tag ct ON ct.id = so_tag.tag_id"""
        return res

    def _group_by_sale(self):
        # groub_by with tag field
        res = super()._group_by_sale()
        res += """,
            ct.name"""
        return res
