# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    partner_id = fields.Many2one("res.partner", "Contact", related="move_dest_ids.group_id.sale_id.partner_id")
    brand_ids = fields.Many2many("product.attribute.value", string="Brand", readonly=True)
    delivery_date = fields.Datetime(related="move_dest_ids.group_id.sale_id.commitment_date", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        brand_attribute = self.env.ref("ortholite_account_mrp_fields.product_attribute_brand_radio")
        if vals_list:
            for vals in vals_list:
                attribute_values = self.product_id.browse(vals['product_id']).mapped('attribute_line_ids.value_ids').filtered(lambda value_id: value_id.attribute_id == brand_attribute)
                if attribute_values:
                    vals['brand_ids'] = attribute_values
        return super().create(vals_list)
