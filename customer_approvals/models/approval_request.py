# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    partner_id = fields.Many2one('res.partner', 'Name')
    contacts_type = fields.Selection(related='partner_id.contacts_type')
