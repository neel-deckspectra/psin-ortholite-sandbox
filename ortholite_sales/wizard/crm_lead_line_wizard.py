# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _

class CrmLeadWizard(models.TransientModel):
    _name = 'crm.lead.wizard'
    _description = "CRM Lead Wizard"

    lead_line_ids = fields.One2many(comodel_name="crm.lead.line.wizard", inverse_name="lead_id", string="Lead Lines")
    opportunity_type = fields.Selection([
        ('new_opportunity', 'New Opportunity'),
        ('direct', 'Direct Sale'),
        ('forecast', 'Forecast Sale')
    ], default='new_opportunity', string='Opportunity Type')

    def action_create_quotation(self):
        # create quotation
        ctx = self._context.copy()
        crm_lead_wizard_vals = []
        sale_order = False
        if ctx.get('active_model') == 'crm.lead' and ctx.get('active_id'):
            crm_lead_rec = self.env['crm.lead'].browse(ctx.get('active_id'))
            sale_order_vals = {
                'opportunity_id': crm_lead_rec.id,
                'partner_id': crm_lead_rec.partner_id.id,
                'campaign_id': crm_lead_rec.campaign_id.id,
                'medium_id': crm_lead_rec.medium_id.id,
                'origin': crm_lead_rec.name,
                'source_id': crm_lead_rec.source_id.id,
                'company_id': crm_lead_rec.company_id.id or crm_lead_rec.env.company.id,
                'tag_ids': [(6, 0, crm_lead_rec.tag_ids.ids)],
            }
            if crm_lead_rec.team_id:
                sale_order_vals['team_id'] = crm_lead_rec.team_id.id
            if crm_lead_rec.user_id:
                sale_order_vals['user_id'] = crm_lead_rec.user_id.id
            sale_order = self.env['sale.order'].sudo().create(sale_order_vals)
            for lead_line in self.lead_line_ids:
                crm_lead_wizard_vals.append({
                    'order_id': sale_order.id,
                    'product_id': lead_line.product_id.id or False,
                    'product_categ_id': lead_line.category_id.id or False,
                    'price_unit': lead_line.price_unit,
                    'product_uom_qty': lead_line.new_qty,
                    'lead_line_id': lead_line.lead_line_id.id,
                })
            sale_order_line = self.env['sale.order.line'].sudo().create(crm_lead_wizard_vals)
        if sale_order:
            action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = sale_order.id
            return action


class CrmLeadLineWizard(models.TransientModel):
    _name = 'crm.lead.line.wizard'
    _description = "Line in CRM Lead Wizard"

    lead_id = fields.Many2one("crm.lead.wizard", string="Lead")
    product_id = fields.Many2one("product.product", string="Product", index=True)
    category_id = fields.Many2one("product.category", string="Product Category", index=True)
    order_qty = fields.Integer(string="Order in Hand")
    forecasted_qty = fields.Integer(string="Forecasted Quantity")
    new_qty = fields.Integer(string="New Order Quantity")
    price_unit = fields.Float(digits="Unit Price")
    product_attribute_value_id = fields.Many2one(comodel_name='product.attribute.value', string="Brand")
    fc_date = fields.Date(string='FC Date')
    lead_line_id = fields.Many2one('crm.lead.line', string='Lead Line')
