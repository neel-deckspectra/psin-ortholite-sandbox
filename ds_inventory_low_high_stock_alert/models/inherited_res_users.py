# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    notify_user = fields.Boolean(string="Notify Stock User")