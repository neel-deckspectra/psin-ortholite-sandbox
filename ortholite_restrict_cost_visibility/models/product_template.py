# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import models, fields, api, exceptions, tools, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @tools.ormcache()
    def _get_default_uom_id(self):
        # Set default as null
        return True

    @tools.ormcache()
    def _get_default_category_id(self):
        # Set default as null
        return True

    is_fg_product = fields.Boolean("Finished Good")
    is_materials = fields.Boolean("Raw Material")
    is_general_item = fields.Boolean("General Item")
    detailed_type = fields.Selection(default='')
    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.")
    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        change_default=True, default=_get_default_category_id, group_expand='_read_group_categ_id',
        required=True)

    @api.constrains('is_fg_product', 'is_materials', 'is_general_item')
    def _check_fg_product_is_materials(self):
        for rec in self:
            if not rec.is_fg_product and not rec.is_materials and not rec.is_general_item:
                raise ValidationError(_(
                    'Please ensure that at least one checkbox is selected for the product type: "Finished Good" or "Raw Material" or "General Item"'))
