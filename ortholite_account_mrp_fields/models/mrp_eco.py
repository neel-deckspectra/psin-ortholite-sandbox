# -*- coding: utf-8 -*-

from odoo import models, fields


class MrpEco(models.Model):
    _inherit = "mrp.eco"

    quantity = fields.Integer("Quantity")
