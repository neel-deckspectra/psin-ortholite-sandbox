# -*- coding: utf-8 -*-

from odoo import models
from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_category = fields.Many2one("product.category", related="order_line.product_id.categ_id", store=True)

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        vals.update({'brand_ids': [(6, 0, self.tag_ids.ids)]})
        return vals
