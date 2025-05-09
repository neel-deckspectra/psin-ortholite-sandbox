# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    product_categ_id = fields.Many2one("product.category", string="Product Category")

    @api.onchange('product_categ_id')
    def onchange_product_categ_id(self):
        for record in self:
            record.product_id = False
