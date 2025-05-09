# -*- coding: utf-8 -*-

from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    product_categ_id = fields.Many2one(related="product_id.categ_id")



class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    invoice_date = fields.Date(string="Invoice Date")
