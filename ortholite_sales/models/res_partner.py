# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models, _


class ResPartnerCode(models.Model):
    _name = 'res.partner.code'
    _description = 'Customer/Vendor Code'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    type = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor')
    ], default='customer', string='Type')



class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_code_id = fields.Many2one('res.partner.code', string='Category')
    code_type = fields.Selection(related='partner_code_id.type', string='Type')
    customer_pan = fields.Binary(attachment=True, string='PAN')
    customer_certificate_gst = fields.Binary(attachment=True, string='GST Certificate')
    customer_incorporation_certificate = fields.Binary(attachment=True, string='Incorporation Certificate')
    customer_form = fields.Binary(attachment=True, string='Customer Form')
    customer_brands_worked = fields.Binary(attachment=True, string='Brands Worked For')
    customer_ehs_requirements = fields.Binary(attachment=True, string='EHS Requirements ( To be aligned / Approved with EHS)')
    customer_approval_proof = fields.Binary(attachment=True, string='Credit Terms Internal Approval Proof')
    customer_financials_from_toffler = fields.Binary(attachment=True, string='Financials from Toffler (This will be analyzed and attached by Finance)')
    vendor_cancelled_cheque = fields.Binary(attachment=True, string='Cancelled Cheque/Bank Account Details')
    vendor_pan = fields.Binary(attachment=True, string='PAN')
    vendor_gst = fields.Binary(attachment=True, string='GST Certificate')
    vendor_incorporation_certificate = fields.Binary(attachment=True, string='Incorporation Certificate')
    vendor_form = fields.Binary(attachment=True, string='Vendor Form')
    vendor_credit_terms = fields.Binary(attachment=True, string='Credit Terms Internal Approval Proof')
    vendor_price_list = fields.Binary(attachment=True, string='Approved Price List')
    vendor_ehs = fields.Binary(attachment=True, string='EHS Requirements ( To be aligned / Approved with EHS)')
    vendor_msme_certificate = fields.Binary(attachment=True, string='MSME Certificate')
    vendor_registration = fields.Char(string='MSME Registration')

    @api.model
    def create(self, vals):
        # Set Customer/Vendor Code.
        res = super(ResPartner, self).create(vals)
        if res.partner_code_id:
            sequence = self.env['ir.sequence'].next_by_code('res.partner')
            res.code = str(res.partner_code_id.code + sequence)
        return res