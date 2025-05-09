# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[
        ('bom', 'Create BoM'),
        ('product', 'Create Product'),
    ])

    @api.constrains('approval_type')
    def _check_duplicate_approval_type(self):
        for record in self:
            if record.approval_type in ['bom', 'product', 'customer'] and self.search_count([
                    ('approval_type', '=', record.approval_type),
                    ('company_id', '=', record.company_id.id),
                ]) > 1:
                raise ValidationError("You can not set 'Approval Type' as a (Customer, BoM and Product).")



class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    bom_id = fields.Many2one('mrp.bom', 'BoM')
    template_id = fields.Many2one('product.template', 'Product')
    categ_id = fields.Many2one('product.category', string='Product Category')



class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_approval_id = fields.Many2one('approval.request')
    request_status = fields.Selection(related="bom_approval_id.request_status", tracking=True, store=True)
    approval_active = fields.Boolean(default="True")
    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], compute="_compute_user_status")
    has_access_to_request = fields.Boolean(string="Has Access To Request", compute="_compute_has_access_to_request")

    @api.depends('bom_approval_id.approver_ids.status')
    def _compute_user_status(self):
        for bom in self:
            bom.user_status = bom.bom_approval_id.request_status

    def _compute_has_access_to_request(self):
        is_approval_user = self.env.user.has_group('approvals.group_approval_user')
        for bom in self:
            bom.has_access_to_request = bom.bom_approval_id.sudo().request_owner_id == self.env.user and is_approval_user

    @api.model_create_multi
    def create(self, vals_list):
        bom_rec = super(MrpBom, self).create(vals_list)
        domain = [('approval_type', '=', 'bom')]
        if bom_rec.company_id:
            domain += [('company_id', '=', bom_rec.company_id.id)]
        else:
            domain += [('company_id', '=', self.env.company.id)]
        bom_category_rec = self.env['approval.category'].sudo().search(domain, limit=1)
        approver = False
        if bom_category_rec:
            if not bom_category_rec.approver_ids:
                raise ValidationError(_("Request approver not set, Please contact your administrator for assistance"))
            if not bom_category_rec.sudo().active:
                if not bom_category_rec.sudo().approver_ids or not bom_category_rec.sudo().approver_ids.filtered(lambda approver: approver.user_id == self.env.user):
                    approver = self.env['approval.category.approver'].create({
                        'user_id': self.env.user.id,
                        'category_id': bom_category_rec.sudo().id
                    })
                for bom in bom_rec:
                    approval_req = self.env['approval.request'].create({
                        'name': bom.display_name,
                        'category_id': bom_category_rec.sudo().id,
                        'bom_id': bom.id,
                        'company_id': self.env.company_id
                    })
                    bom.update({'bom_approval_id': approval_req.id, 'approval_active': False})
                    approval_req.action_confirm()
                    approval_req.action_approve()
                    if approver:
                        approver.unlink()
            else:
                for bom in bom_rec:
                    approval_req = self.env['approval.request'].sudo().create({
                        'name': bom.display_name,
                        'category_id': bom_category_rec.id,
                        'bom_id': bom.id,
                        'company_id': self.env.company.id
                    })
                    bom.update({'bom_approval_id': approval_req.id, 'approval_active': True})
        return bom_rec

    def approval_action_confirm(self):
        for rec in self:
            domain = [('approval_type', '=', 'bom')]
            if rec.company_id:
                domain += [('company_id', '=', rec.company_id.id)]
            else:
                domain += [('company_id', '=', self.env.company.id)]
            bom_category_rec = self.env['approval.category'].sudo().search(domain, limit=1)
            if bom_category_rec:
                if not bom_category_rec.approver_ids:
                    raise ValidationError(_("Request approver not set, Please contact your administrator for assistance"))
            if not rec.bom_approval_id:
                approval_req = self.env['approval.request'].sudo().create({
                    'name': rec.display_name,
                    'category_id': bom_category_rec.id,
                    'bom_id': rec.id,
                    'company_id': self.env.company.id
                })
                rec.update({'bom_approval_id': approval_req.id, 'approval_active': True})
                rec.bom_approval_id.action_confirm()
            else:
                rec.bom_approval_id.action_confirm()

    def approval_action_approve(self):
        for rec in self:
            rec.bom_approval_id.action_approve()

    def approval_action_refuse(self):
        for rec in self:
            rec.bom_approval_id.action_refuse()

    def approval_action_withdraw(self):
        for rec in self:
            rec.bom_approval_id.action_withdraw()

    def approval_action_draft(self):
        for rec in self:
            rec.bom_approval_id.action_draft()

    def approval_action_cancel(self):
        for rec in self:
            rec.bom_approval_id.action_cancel()



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_approval_id = fields.Many2one('approval.request')
    request_status = fields.Selection(related="template_approval_id.request_status", tracking=True, store=True)
    approval_active = fields.Boolean(default="True")
    user_status = fields.Selection([
        ('new', 'New'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], compute="_compute_user_status")
    has_access_to_request = fields.Boolean(string="Has Access To Request", compute="_compute_has_access_to_request")

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Show only approval product
        domain = domain.copy()
        if self._context.get('is_only_approval'):
            domain.append((('request_status', '=', 'approved')))
        return super()._search(domain, offset, limit, order, access_rights_uid)

    @api.depends('template_approval_id.approver_ids.status')
    def _compute_user_status(self):
        for template in self:
            template.user_status = template.template_approval_id.request_status

    def _compute_has_access_to_request(self):
        is_approval_user = self.env.user.has_group('approvals.group_approval_user')
        for template in self:
            template.has_access_to_request = template.template_approval_id.sudo().request_owner_id == self.env.user and is_approval_user

    @api.model_create_multi
    def create(self, vals_list):
        template_rec = super(ProductTemplate, self).create(vals_list)
        domain = [('approval_type', '=', 'product')]
        if template_rec.company_id:
            domain += [('company_id', '=', template_rec.company_id.id)]
        else:
            domain += [('company_id', '=', self.env.company.id)]
        template_category_rec = self.env['approval.category'].sudo().search(domain, limit=1)
        approver = False
        if template_category_rec:
            if not template_category_rec.approver_ids:
                raise ValidationError(_("Request approver not set, Please contact your administrator for assistance"))
            if not template_category_rec.sudo().active:
                if not template_category_rec.sudo().approver_ids or not template_category_rec.sudo().approver_ids.filtered(lambda approver: approver.user_id == self.env.user):
                    approver = self.env['approval.category.approver'].create({
                        'user_id': self.env.user.id,
                        'category_id': template_category_rec.sudo().id
                    })
                for template in template_rec:
                    approval_req = self.env['approval.request'].create({
                        'name': template.display_name,
                        'category_id': template_category_rec.sudo().id,
                        'template_id': template.id,
                        'company_id': self.env.company_id,
                        'categ_id': template_rec.categ_id.id or False,
                    })
                    template.update({'template_approval_id': approval_req.id, 'approval_active': False})
                    approval_req.action_confirm()
                    approval_req.action_approve()
                    if approver:
                        approver.unlink()
            else:
                for template in template_rec:
                    approval_req = self.env['approval.request'].sudo().create({
                        'name': template.display_name,
                        'category_id': template_category_rec.id,
                        'template_id': template.id,
                        'company_id': self.env.company.id,
                        'categ_id': template_rec.categ_id.id or False,
                    })
                    template.update({'template_approval_id': approval_req.id, 'approval_active': True})
        return template_rec

    def approval_action_confirm(self):
        for rec in self:
            domain = [('approval_type', '=', 'product')]
            if rec.company_id:
                domain += [('company_id', '=', rec.company_id.id)]
            else:
                domain += [('company_id', '=', self.env.company.id)]
            template_category_rec = self.env['approval.category'].sudo().search(domain, limit=1)
            if template_category_rec:
                if not template_category_rec.approver_ids:
                    raise ValidationError(_("Request approver not set, Please contact your administrator for assistance"))
            if not rec.template_approval_id:
                approval_req = self.env['approval.request'].sudo().create({
                    'name': rec.display_name,
                    'category_id': template_category_rec.id,
                    'template_id': rec.id,
                    'company_id': self.env.company.id,
                    'categ_id': rec.categ_id.id or False,
                })
                rec.update({'template_approval_id': approval_req.id, 'approval_active': True})
                rec.template_approval_id.categ_id = rec.categ_id.id or False
                rec.template_approval_id.action_confirm()
            else:
                rec.template_approval_id.categ_id = rec.categ_id.id or False
                rec.template_approval_id.action_confirm()

    def approval_action_approve(self):
        for rec in self:
            rec.template_approval_id.action_approve()

    def approval_action_refuse(self):
        for rec in self:
            rec.template_approval_id.action_refuse()

    def approval_action_withdraw(self):
        for rec in self:
            rec.template_approval_id.action_withdraw()

    def approval_action_draft(self):
        for rec in self:
            rec.template_approval_id.action_draft()

    def approval_action_cancel(self):
        for rec in self:
            rec.template_approval_id.action_cancel()



class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        # Show only approval product
        domain = domain.copy()
        if self._context.get('is_only_approval'):
            domain.append((('request_status', '=', 'approved')))
        return super()._search(domain, offset, limit, order, access_rights_uid)

    def approval_action_confirm(self):
        for rec in self:
            rec.template_approval_id.categ_id = rec.categ_id.id or False
            rec.template_approval_id.action_confirm()

    def approval_action_approve(self):
        for rec in self:
            rec.template_approval_id.action_approve()

    def approval_action_refuse(self):
        for rec in self:
            rec.template_approval_id.action_refuse()

    def approval_action_withdraw(self):
        for rec in self:
            rec.template_approval_id.action_withdraw()

    def approval_action_draft(self):
        for rec in self:
            rec.template_approval_id.action_draft()

    def approval_action_cancel(self):
        for rec in self:
            rec.template_approval_id.action_cancel()



class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.depends('country_id')
    def _get_is_country_india(self):
        # check country
        for rec in self:
            rec.is_country_india = False
            if rec.country_id and rec.country_id.code == 'IN':
                rec.is_country_india = True

    is_country_india = fields.Boolean(
        compute=_get_is_country_india, string="Is India Country", help='Check Country is India.')