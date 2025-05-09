# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DefectEntry(models.Model):
    _name = "defect.entry"
    _description = "Defect Entry"
    _rec_name = "sale_order_id"

    datetime = fields.Datetime(string="Datetime", default=lambda self: fields.Datetime.now())
    sale_order_id = fields.Many2one("sale.order", string="SO Number")
    product_id = fields.Many2one("product.product", string="Product")
    product_category_id = fields.Many2one('product.category', name='Product Category', related='product_id.categ_id', store=True)
    defect_section_id = fields.Many2one('defect.section', string="Section")
    defect_library_id = fields.Many2one('defect.library', name='Defect Selection')
    quantity = fields.Float(string='Quantity')
    product_uom = fields.Many2one(
        'uom.uom', 'Unit of Measure', related='product_id.uom_id', store=True)



class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Get product base on sale order in defect entr.
        if self._context.get('defect_entry_so_id'):
            sale_order_rec = self.env['sale.order'].browse(self._context.get('defect_entry_so_id'))
            domain = domain.copy()
            domain.append((('id', 'in', sale_order_rec.order_line.mapped('product_id').ids)))
        return super()._search(domain, offset, limit, order, access_rights_uid)



class DefectLibrary(models.Model):
    _name = "defect.library"
    _description = "Defect Library"
    _rec_name = 'name'

    name = fields.Char('Name')



class DefectSection(models.Model):
    _name = "defect.section"
    _description = "Defect Section"
    _rec_name = 'name'

    name = fields.Char('Name')