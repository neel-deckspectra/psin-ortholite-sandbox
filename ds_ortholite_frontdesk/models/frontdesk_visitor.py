from odoo import models, fields, api, _, SUPERUSER_ID


class FrontdeskVisitor(models.Model):
    _inherit = "frontdesk.visitor"

    visiting_reason = fields.Char("Reason For Visiting")
    govt_id = fields.Char("Govt. ID")
    oin_id_visitor_number = fields.Char("OIN ID Visitor Number")
    electronic_device = fields.Char("Electronic Device")
    host_ids = fields.Many2many('hr.employee', string='Host Name', domain="[]")
