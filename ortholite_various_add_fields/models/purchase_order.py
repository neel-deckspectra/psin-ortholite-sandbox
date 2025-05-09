# -*- coding: utf-8 -*-

from odoo import api, models, fields


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange('partner_id')
    def onchange_partner_set_incoterm(self):
        self.incoterm_id = False
        if self.partner_id.incoterm_id:
            self.incoterm_id = self.partner_id.incoterm_id



class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    product_attribute_value_id = fields.Many2one(comodel_name='product.attribute.value', string="Brand")



class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    float_value = fields.Float(string='Float Values')

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Get brand attribute values.
        brand_attribute_value_id = self.env.ref(
            "ortholite_account_mrp_fields.product_attribute_brand_radio", raise_if_not_found=False).id
        domain = domain.copy()
        if self._context.get('is_brand_attribute_value') and brand_attribute_value_id:
            domain.append((('attribute_id', '=', brand_attribute_value_id)))
        if self._context.get('is_get_attribute_value_based_on_template_id') and brand_attribute_value_id:
            template_rec = self.env['product.template'].browse(self._context.get('is_get_attribute_value_based_on_template_id'))
            product_template_attribute_line_rec = template_rec.attribute_line_ids.filtered(
                lambda line: line.attribute_id.id == brand_attribute_value_id)
            domain.append(('id', 'in', product_template_attribute_line_rec.mapped('value_ids').ids))
        return super()._search(domain, offset, limit, order, access_rights_uid)
