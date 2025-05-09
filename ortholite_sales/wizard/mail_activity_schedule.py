# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'

    is_visit = fields.Boolean(string="Is a Visit", related='activity_type_id.is_visit')
    product_attribute_value_id = fields.Many2one(comodel_name='product.attribute.value', string="Brand")
    season_id = fields.Many2one('season', string="Season")
    purpose_of_visit = fields.Text(string="Purpose of Visit")
    factory_contact = fields.Text(string="Factory Contact")
    competitor_info = fields.Text(string="Competitor Info")
    grades_used = fields.Text(string="Ortholite Grades Used")
    remarks = fields.Text(string="Remarks")
    partner_ids = fields.Many2many('res.partner', string="Customer")

    @api.onchange('activity_type_id')
    def onchange_activity_type_remove_season(self):
        self.product_attribute_value_id = self.season_id = self.factory_contact = self.purpose_of_visit = self.competitor_info = self.grades_used = self.remarks = False

    def _action_schedule_activities(self):
        # Overwriting this method to update details in mail activity
        values = super()._action_schedule_activities()
        if self.is_visit and self.res_model == 'res.partner':
            for value in values:
                value.update({
                    'is_visit': self.is_visit,
                    'product_attribute_value_id': self.product_attribute_value_id.id or False,
                    'season_id': self.season_id.id or False,
                    'purpose_of_visit': self.purpose_of_visit,
                    'factory_contact': self.factory_contact,
                    'competitor_info': self.competitor_info,
                    'grades_used': self.grades_used,
                    'remarks': self.remarks,
                })
            for partner in self.partner_ids:
                # create activity for customer
                self.env['mail.activity'].create({
                    'activity_type_id': self.activity_type_id.id,
                    'summary': self.summary,
                    'automated': True,
                    'note': self.note,
                    'date_deadline': self.date_deadline,
                    'res_model_id': self.res_model_id.id,
                    'res_id': partner.id,
                    'is_visit': self.is_visit,
                    'product_attribute_value_id': self.product_attribute_value_id.id or False,
                    'season_id': self.season_id.id or False,
                    'purpose_of_visit': self.purpose_of_visit,
                    'factory_contact': self.factory_contact,
                    'competitor_info': self.competitor_info,
                    'grades_used': self.grades_used,
                    'remarks': self.remarks,
                })
        return values