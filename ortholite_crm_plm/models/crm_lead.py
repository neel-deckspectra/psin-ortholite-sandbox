
# -*- coding: utf-8 -*-

from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    plm_count = fields.Integer(compute='_compute_plm_data', string="Number of PLMs")
    product_category_ids = fields.Many2many('product.category', string="Product Category")
    product_attribute_ids = fields.Many2many('product.attribute.value', string="Product Attribute")

    def _compute_plm_data(self):
        for lead in self:
            lead.plm_count = lead.env['mrp.eco'].search_count([('crm_opportunity_id', '=', lead.id)])

    def action_view_plm(self):
        return {
            'name': 'PLM',
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.eco',
            'domain': [('crm_opportunity_id', '=', self.id )],
            'context': {'default_crm_opportunity_id': self.id, 'default_contact_id': self.partner_id.id, 'default_product_category_ids': self.product_category_ids.ids, 'default_product_attribute_ids': self.product_attribute_ids.ids},
            'view_mode': 'tree,form',
        }
