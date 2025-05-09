# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
import pytz



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_categ_id = fields.Many2one(related="product_id.categ_id")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    employee_id = fields.Many2one('hr.employee', string='Prepared By')

    def get_datetime(self):
        user_tz = self.env.user.tz or 'UTC'
        user_time = datetime.now(pytz.timezone(user_tz))
        return user_time.strftime('%d-%m-%Y %H:%M:%S')
