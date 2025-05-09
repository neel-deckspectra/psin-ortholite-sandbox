# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'


    def _is_from_single_value_line(self, only_active=True):
        # Override to return false to show description for single attribute value.
        self.ensure_one()
        all_values = self.attribute_line_id.product_template_value_ids
        if only_active:
            all_values = all_values._only_active()
        return False