# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    qr_code = fields.Binary("QR Code", compute='generate_qr_code')
    sr_number = fields.Char(string="SR Number", copy=False, readonly=True, default='New')
    workcenter_id = fields.Many2one('mrp.workcenter', string='Location')
    equipment_count = fields.Integer(compute='_compute_equipment_count', string='Equipment')
    code = fields.Char(string="Code")

    @api.model
    def create(self, vals):
        res = super(AccountAsset, self).create(vals)
        if res.model_id and res.model_id.code:
            sequence = self.env['ir.sequence'].next_by_code('account.asset') or '/'
            res.sr_number = str('OIN/' + res.model_id.code + '/' + res.name + '/' + sequence)
        return res

    def _compute_equipment_count(self):
        for record in self:
            record.equipment_count = self.env['maintenance.equipment'].search_count([
                ('account_asset_id', '=', self.id)
            ])

    def generate_qr_code(self):
        for rec in self:
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
                qr.add_data("Name: ")
                qr.add_data(rec.name)
                qr.add_data(", SR Number: ")
                qr.add_data(rec.sr_number)
                qr.add_data(", Location: ")
                qr.add_data(rec.workcenter_id.name)
                qr.add_data(", Acquisition Date: ")
                qr.add_data(rec.acquisition_date)
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code': qr_image})

    def open_equipment(self):
        return {
            'name': _('Equipment'),
            'view_mode': 'tree,form',
            'res_model': 'maintenance.equipment',
            'type': 'ir.actions.act_window',
            'domain': [('account_asset_id', '=', self.id)],
            'context': dict(self._context, create=False),
        }



class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    account_asset_id = fields.Many2one("account.asset", "Asset")



class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    vendor_bill_id = fields.Many2one(
        'account.move', 'Vendor Bill', copy=False, domain=[('move_type', '=', 'in_invoice')])



class AccountMove(models.Model):
    _inherit = 'account.move'

    maintenance_request_count = fields.Integer("Maintenance Request Count", compute='_compute_maintenance_request_ids')
    maintenance_request_ids = fields.Many2many(
        'maintenance.request', compute='_compute_maintenance_request_ids', string='Maintenance Requests')

    def _compute_maintenance_request_ids(self):
        for move in self:
            maintenance_request_ids = self.env['maintenance.request'].sudo().search([
                ('vendor_bill_id', '=', move.id),
            ])
            move.maintenance_request_count = len(maintenance_request_ids)
            move.maintenance_request_ids = maintenance_request_ids.ids

    def action_open_maintenance_request(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Requests'),
            'res_model': 'maintenance.request',
            'context': {'create': False},
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.maintenance_request_ids.ids)],
        }