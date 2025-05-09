# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _



class Season(models.Model):
    _name = 'season'
    _description = 'Season'

    name = fields.Char(string='Season Name', required=True)