# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('name')
    def _check_unique_product_name(self):
        for record in self:
            if self.search_count([('name', '=', record.name)]) > 1:
                raise exceptions.ValidationError("Product name must be unique.")

    def _prepare_attribute_values(self, attribute):
        self.ensure_one()
        return {
            'attribute_id': attribute.id,
        }

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        attribute_vals = []
        for record in self:
            if not self._origin.id:
                record.attribute_line_ids = False
                if record.categ_id and record.categ_id.attributes_ids:
                    product_attribute_ids = record.attribute_line_ids.mapped('attribute_id').ids
                    attributes = record.categ_id.attributes_ids.filtered(
                        lambda line: line.id not in product_attribute_ids)
                    attribute_data = [fields.Command.clear()]
                    attribute_data += [
                        fields.Command.create(record._prepare_attribute_values(attribute)) for attribute in attributes
                    ]
                    record.attribute_line_ids = attribute_data



class ProductCategory(models.Model):
    _inherit = 'product.category'

    code = fields.Char('Code', copy=False)
    attributes_ids = fields.Many2many('product.attribute', string='Attributes')



class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        # Set Internal Reference based on Category Code
        res = super(ProductProduct, self).create(vals)
        if res.categ_id and res.categ_id.code:
            sequence = self.env['ir.sequence'].next_by_code('product.internal.reference')
            res.default_code = str(res.categ_id.code + '-' + sequence)
        return res