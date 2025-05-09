# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from datetime import date


class PurchaseRequest(models.Model):
    _inherit = "purchase.request"

    @api.onchange('requested_by')
    def onchange_requested_by_set_assigned_to(self):
        # Set approver
        hr_employee_obj = self.env['hr.employee']
        for record in self:
            record.assigned_to = False
            if record.requested_by:
                employee_rec = hr_employee_obj.sudo().search([
                    ('user_id', '=', record.requested_by.id),
                    ('parent_id.user_id.groups_id', '=', self.env.ref("purchase_request.group_purchase_request_manager").id),
                ], limit=1)
                if employee_rec and employee_rec.parent_id and employee_rec.parent_id.user_id:
                    record.assigned_to = employee_rec.parent_id.user_id.id

    def button_to_approve(self):
        res = super().button_to_approve()
        # Send mail
        if self.assigned_to:
            self.activity_schedule('approvals.mail_activity_data_approval', user_id=self.assigned_to.id)
        return res

    @api.model
    def get_fiscal_year_name(self):
        today = date.today()
        year = today.year
        if today.month < 4:
            start_year = year - 1
            end_year = year
        else:
            start_year = year
            end_year = year + 1
        return f"{start_year % 100:02d}-{end_year % 100:02d}"

    @api.model
    def _get_default_name(self):
        # Override to change sequence format
        sequence = self.env["ir.sequence"].next_by_code("purchase.request")
        reference = str('PR/' + self.get_fiscal_year_name() + '/' + sequence)
        return reference