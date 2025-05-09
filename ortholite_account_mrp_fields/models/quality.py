# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "quality.check"

    so_source = fields.Char(string="SO Source", related="picking_id.sale_id.display_name", store=True)
    po_source = fields.Char(string="PO Source", related="picking_id.purchase_id.display_name", store=True)
    product_category = fields.Many2one(related="product_id.categ_id", store=True)
    brand_ids = fields.Many2many(string="Brand", comodel_name="crm.tag", compute="_compute_brand_ids", store=True)
    delivery_date = fields.Datetime(related="picking_id.sale_id.commitment_date", store=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        if vals_list:
            for vals in vals_list:
                if 'picking_id' in  vals:
                    production_id = self.picking_id.browse(vals['picking_id']).group_id.mrp_production_ids
                    if production_id.mrp_production_source_count:
                        vals['production_id'] = production_id._get_sources().id
                    else:
                        vals['production_id'] = production_id.id
        return super().create(vals_list)

    @api.depends('picking_id.sale_id.tag_ids')
    def _compute_brand_ids(self):
        for rec in self:
            rec.brand_ids = rec.picking_id.sale_id.tag_ids
