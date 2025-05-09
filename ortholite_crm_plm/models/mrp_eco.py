# -*- coding: utf-8 -*-

from odoo import api, models, fields


class MrpEco(models.Model):
    _inherit = "mrp.eco"

    crm_opportunity_id = fields.Many2one('crm.lead', string="CRM Opportunity")
    contact_id = fields.Many2one('res.partner', string='Contact')
    product_category_ids = fields.Many2many('product.category', string="Product Category")
    product_attribute_ids = fields.Many2many('product.attribute.value', string="Product Attribute")
    size = fields.Char(string='Size')
    status = fields.Selection([
        ('Dispatched', 'Dispatched'),
        ('Hold', 'Hold')
    ], string='Status', copy=False)
    feedback = fields.Selection([
        ('Order Received', 'Order Received'),
        ('Waiting For Feedback', 'Waiting For Feedback'),
        ('Drop', 'Drop')
    ], string='Feedback', copy=False)
    shipped = fields.Integer("Shipped")
    dispatched_date = fields.Date(string='Dispatched Date')

    @api.onchange("status")
    def onchange_status(self):
        for rec in self:
            rec.dispatched_date = False
            if rec.status == 'Dispatched':
                rec.dispatched_date = fields.Date.today()
