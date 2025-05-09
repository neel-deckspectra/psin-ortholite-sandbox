# -*- coding: utf-8 -*-

from odoo import models, fields


class Partner(models.Model):
    _inherit = "res.partner"

    incoterm_id = fields.Many2one(
        'account.incoterms', 'Incoterm', help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")