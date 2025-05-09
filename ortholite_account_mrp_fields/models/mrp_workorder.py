# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    partner_id = fields.Many2one("res.partner", "Contact", related="production_id.partner_id", store=True)
    brand_ids = fields.Many2many(comodel_name="product.attribute.value", compute ="_compute_brand_ids", store=True)

    @api.depends("production_id.brand_ids")
    def _compute_brand_ids(self):
        for rec in self:
            rec.brand_ids = rec.production_id.brand_ids
