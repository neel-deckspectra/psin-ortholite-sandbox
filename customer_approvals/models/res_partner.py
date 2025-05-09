# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer_approval = fields.Many2one('approval.request')
    request_status = fields.Selection(related="customer_approval.request_status", tracking=True, store=True)
    approval_active = fields.Boolean(default="True")
    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], compute="_compute_user_status")
    has_access_to_request = fields.Boolean(string="Has Access To Request", compute="_compute_has_access_to_request")
    contacts_type = fields.Selection([
        ('customer', 'Customer'),
        ('Vendor', 'Vendor')
    ],string='Contact Type', default=None, copy=False)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if args:
    #         args += [('request_status', '=', 'approved'), ('customer_approval', '!=', False)]
    #     return super(ResPartner, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.depends('customer_approval.approver_ids.status')
    def _compute_user_status(self):
        for partner in self:
            partner.user_status = partner.customer_approval.request_status
            # partner.user_status = partner.customer_approval.sudo().approver_ids.filtered(lambda approver: approver.user_id == self.env.user).status

    def _compute_has_access_to_request(self):
        is_approval_user = self.env.user.has_group('approvals.group_approval_user')
        for partner in self:
            partner.has_access_to_request = partner.customer_approval.sudo().request_owner_id == self.env.user and is_approval_user

    @api.model_create_multi
    def create(self, vals_list):
        res_partner = super(ResPartner, self).create(vals_list)
        domain = [('approval_type', '=', 'customer')]
        if res_partner.company_id:
            domain += [('company_id', '=', res_partner.company_id.id)]
        else:
            domain += [('company_id', '=', self.env.company.id)]
        partner_cat = self.env['approval.category'].sudo().search(domain, limit=1)
        approver = False
        if partner_cat:
            if not partner_cat.approver_ids:
                raise ValidationError(_("Request approver not set, Please contact your administrator for assistance"))
            if not partner_cat.sudo().active:
                if not partner_cat.sudo().approver_ids or not partner_cat.sudo().approver_ids.filtered(lambda approver: approver.user_id == self.env.user):
                    approver = self.env['approval.category.approver'].create({
                        'user_id': self.env.user.id,
                        'category_id': partner_cat.sudo().id})
                for partner in res_partner:
                    approval_req = self.env['approval.request'].create({
                        'name': partner.display_name,
                        'category_id': partner_cat.sudo().id,
                        'partner_id': partner.id,
                        'company_id': self.env.company_id
                    })
                    partner.update({'customer_approval': approval_req.id, 'approval_active': False})
                    approval_req.action_confirm()
                    approval_req.action_approve()
                    if approver:
                        approver.unlink()
            else:
                for partner in res_partner:
                    approval_req = self.env['approval.request'].sudo().create({
                        'name': partner.display_name,
                        'category_id': partner_cat.id,
                        'partner_id': partner.id,
                        'company_id': self.env.company.id
                    })
                    partner.update({'customer_approval': approval_req.id, 'approval_active': True})
        return res_partner

    def approval_action_confirm(self):
        for rec in self:
            domain = [('approval_type', '=', 'customer')]
            if rec.company_id:
                domain += [('company_id', '=', rec.company_id.id)]
            else:
                domain += [('company_id', '=', self.env.company.id)]
            partner_cat = self.env['approval.category'].sudo().search(domain, limit=1)
            if partner_cat:
                if not partner_cat.approver_ids:
                    raise ValidationError(_("Request approver not set, Please contact your administrator for assistance"))
            if not rec.customer_approval:
                approval_req = self.env['approval.request'].sudo().create({
                    'name': rec.display_name,
                    'category_id': partner_cat.id,
                    'partner_id': rec.id,
                    'company_id': self.env.company.id
                })
                rec.update({'customer_approval': approval_req.id, 'approval_active': True})
                rec.customer_approval.action_confirm()
            else:
                rec.customer_approval.action_confirm()

    def approval_action_approve(self):
        for rec in self:
            rec.customer_approval.action_approve()

    def approval_action_refuse(self):
        for rec in self:
            rec.customer_approval.action_refuse()

    def approval_action_withdraw(self):
        for rec in self:
            rec.customer_approval.action_withdraw()

    def approval_action_draft(self):
        for rec in self:
            rec.customer_approval.action_draft()

    def approval_action_cancel(self):
        for rec in self:
            rec.customer_approval.action_cancel()
