# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_categ_id = fields.Many2one(related="product_id.categ_id")
