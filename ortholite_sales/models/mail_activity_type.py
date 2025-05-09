# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    is_visit = fields.Boolean(string="Is a Visit")

    @api.constrains('is_visit')
    def _check_duplicate_visit(self):
        for record in self:
            if self.search_count([('is_visit', '=', True)]) > 1:
                raise ValidationError("You can not set 'Is a Visit' with multiple records.")

    def unlink(self):
        for record in self:
            if record.is_visit:
                raise ValidationError("You can not delete records with set 'Is a Visit'.")
        return super().unlink()



class MailActivity(models.Model):
    _inherit = "mail.activity"

    is_visit = fields.Boolean(string="Is a Visit", related='activity_type_id.is_visit')
    product_attribute_value_id = fields.Many2one(comodel_name='product.attribute.value', string="Brand")
    season_id = fields.Many2one('season', string="Season")
    purpose_of_visit = fields.Text(string="Purpose of Visit")
    factory_contact = fields.Text(string="Factory Contact")
    competitor_info = fields.Text(string="Competitor Info")
    grades_used = fields.Text(string="Ortholite Grades Used")
    remarks = fields.Text(string="Remarks")

    @api.onchange('activity_type_id')
    def onchange_activity_type_remove_season(self):
        self.product_attribute_value_id = self.season_id = self.factory_contact = self.purpose_of_visit = self.competitor_info = self.grades_used = self.remarks = False