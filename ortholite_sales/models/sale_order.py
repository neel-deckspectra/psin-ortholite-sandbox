# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # Set validation if product bom are not created.
        res = super(SaleOrder, self).action_confirm()
        product_category_ids = self.env['product.category'].sudo().search([
            ('name', 'in', ['Covered Flat Sheet', 'Die cut', 'INSOLE'])
        ])
        mrp_bom_obj = self.env['mrp.bom']
        for so in self:
            # order line with (Covered Flat Sheet, Die cut and INSOLE) category.
            order_line = so.order_line.filtered(lambda line: line.product_template_id.categ_id.id in product_category_ids.ids)
            for line in order_line:
                bom_rec = mrp_bom_obj.sudo().search([
                    ('product_tmpl_id', '=', line.product_template_id.id),
                    ('request_status', '=', 'approved'),
                ])
                if not bom_rec:
                    raise ValidationError(_(
                        f"No Bill of Materials (BoM) found for the product: {line.product_template_id.name}, Please create a BoM before proceeding."))
        return res