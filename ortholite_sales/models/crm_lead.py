# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.exceptions import AccessError, UserError
import re

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    fc_type = fields.Selection([
        ('buy_plan', 'Buy Plan'),
        ('domestic', 'Domestic')
    ], default=False, string='FC Type')
    season_id = fields.Many2one('season', string="Season")
    customer_group_id = fields.Many2one('res.partner', string="Customer Group")
    opportunity_type = fields.Selection([
        ('new_opportunity', 'New Opportunity'),
        ('direct', 'Direct Sale'),
        ('forecast', 'Forecast Sale')
    ], default='new_opportunity', string='Opportunity Type')

    def action_sale_quotations_new(self):
        # override this method to open wizars and create quotations
        if not self.partner_id:
            raise UserError(_('Please select customer.'))
        crm_lead_wizard_vals = []
        crm_lead_wizard_rec = self.env['crm.lead.wizard'].sudo().create({'opportunity_type': self.opportunity_type})
        so_line_obj = self.env['sale.order.line']
        for lead_line in self.lead_line_ids.filtered(lambda line: not line.display_type):
            crm_lead_wizard_vals.append({
                'lead_id': crm_lead_wizard_rec.id or False,
                'product_id': lead_line.product_id.id or False,
                'category_id': lead_line.category_id.id or False,
                'price_unit': lead_line.price_unit or 0.0,
                'order_qty': lead_line.order_qty,
                'forecasted_qty': lead_line.product_qty,
                'product_attribute_value_id': lead_line.product_attribute_value_id.id or False,
                'fc_date': lead_line.fc_date or False,
                'lead_line_id': lead_line.id,
            })
        crm_lead_wizard_line_rec = self.env['crm.lead.line.wizard'].sudo().create(crm_lead_wizard_vals)
        return {
            'name': _('Create New Quotation'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'crm.lead.wizard',
            'target': 'new',
            'res_id': crm_lead_wizard_rec.id,
            'view_id': self.env.ref('ortholite_sales.crm_lead_wizard_wizard_form_view').id,
        }

    @api.onchange("opportunity_type")
    def _onchange_opportunity_type(self):
        self.fc_type = self.season_id = self.customer_group_id = False

    @api.model_create_multi
    def create(self, vals):
        records = super(CrmLead, self).create(vals)
        for record in records:
            if record.opportunity_type and record.opportunity_type == 'forecast' and not record.fc_type:
                raise ValidationError(_("FC Type is required for Opportunity Type Forecast Sale"))
        return records

    def write(self, vals):
        res = super().write(vals)
        if self.opportunity_type and self.opportunity_type == 'forecast' and not self.fc_type:
            raise ValidationError(_("FC Type is required for Opportunity Type Forecast Sale"))
        return res



class CrmLeadLine(models.Model):
    _inherit = "crm.lead.line"

    order_qty = fields.Integer(string="Order in Hand", compute='_compute_order_qty')
    display_type = fields.Selection(selection=[
        ('line_section', "Section"),
        ('line_note', "Note"),
    ],default=False)
    product_attribute_value_id = fields.Many2one(comodel_name='product.attribute.value', string="Brand")
    fc_date = fields.Date(string='FC Date')

    @api.depends('lead_id.order_ids')
    def _compute_order_qty(self):
        so_line_obj = self.env['sale.order.line']
        for rec in self:
            so_line_rec = so_line_obj.sudo().search([
                ('order_id', 'in', rec.lead_id.order_ids.ids),
                ('order_id.partner_id', '=', rec.lead_id.partner_id.id),
                ('product_id', '=', rec.product_id.id),
                ('lead_line_id', '=', rec.id),
            ])
            rec.order_qty = sum(so_line_rec.mapped('product_uom_qty'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('display_type'):
                vals.update(product_id=False, product_qty=0)
        return super().create(vals_list)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a product details line. Instead you should delete the current line and create a new line of the proper type."))
        return super().write(values)

    @api.onchange("product_id")
    def _onchange_product_set_brand_id(self):
        # set brand values based on product attribute value
        self.product_attribute_value_id = False
        brand_attribute_value_id = self.env.ref(
            "ortholite_account_mrp_fields.product_attribute_brand_radio", raise_if_not_found=False).id
        attribute_brand = self.product_id.product_template_variant_value_ids.filtered(
            lambda line: line.attribute_id.id == brand_attribute_value_id)
        if attribute_brand:
            self.product_attribute_value_id = attribute_brand[0].product_attribute_value_id.id



class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_customer_group = fields.Boolean(string="Is a Customer Group")
    code = fields.Char(string="Code")
    phone_code = fields.Char(string="Country Calling Code")

    @api.constrains('email')
    def _check_email(self):
        for rec in self:
            if rec.email:
                match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', rec.email)
                if match == None:
                    raise ValidationError('Invalid email format. Please enter a valid email.')

    @api.constrains('mobile')
    def _check_mobile(self):
        for rec in self:
            if rec.mobile:
                pattern = re.compile(r'^\+?1?\d{6,15}$')
                if not pattern.match(rec.mobile):
                    raise ValidationError("Invalid phone number format. Please enter a valid phone number.")

    @api.onchange("country_id")
    def _onchange_country_id_set_code(self):
        for rec in self:
            if rec.country_id:
                rec.phone_code = '+' + str(rec.country_id.phone_code)

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            self.mobile = self.mobile

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        if self.phone:
            self.phone = self.phone


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    def write(self, vals):
        # Set validation if user change "Brand" name
        if 'name' in vals:
            if self.name == 'Brand':
                raise UserError(_('You are not allowed to change this attribute name.'))
        return super(ProductAttribute, self).write(vals)



class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Get brand attribute values.
        brand_attribute_value_id = self.env.ref(
            "ortholite_account_mrp_fields.product_attribute_brand_radio", raise_if_not_found=False).id
        domain = domain.copy()
        if self._context.get('brand_attribute_value') and brand_attribute_value_id:
            domain.append((('attribute_id', '=', brand_attribute_value_id)))
        return super()._search(domain, offset, limit, order, access_rights_uid)



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lead_line_id = fields.Many2one('crm.lead.line', string='Lead Line')