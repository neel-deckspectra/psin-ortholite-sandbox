# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import re


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        # update source document
        values = super()._prepare_sale_order_data(name, partner, company, direct_delivery_address)
        so_name = ''
        for name in self.origin.split(','):
            # split with -
            order_value = re.split('-',name)[-1]
            # remove spaces
            order_name = order_value.replace(" ", "")
            so_name += (order_name) + ', '
        values.update({'origin': 'OIN3: ' + so_name[:-2]})
        return values