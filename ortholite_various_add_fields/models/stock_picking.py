# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from datetime import datetime, date
import pytz
from odoo.exceptions import ValidationError, AccessError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ortholite_delivery_type = fields.Selection([
        ('returnable', 'Returnable'),
        ('non_returnable', 'Non Returnable')
    ], string='Delivery Type')
    ortholite_issue = fields.Selection([
        ('production', 'Production'),
        ('excess', 'Excess')
    ], string='Issue', default='production')
    po_received_date = fields.Datetime(string='PO Received Date', copy=False)
    grn_sequence = fields.Char(string='GRN', copy=False)

    def get_datetime(self):
        user_tz = self.env.user.tz or 'UTC'
        user_time = datetime.now(pytz.timezone(user_tz))
        return user_time.strftime('%d-%m-%Y %H:%M:%S')


    def check_quality(self):
        # overwrite this method set validation
        self.ensure_one()
        if not self.env.user.has_group('quality.group_quality_manager'):
            raise AccessError(_("You have no access rights to check quality."))
        if not self.po_received_date and self.picking_type_code == 'incoming':
            raise ValidationError(_("Please set the 'PO Received Date' before proceeding to check quality"))
        return super().check_quality()

    def set_po_received_date(self):
        # Set current date and time on po received date.
        for record in self:
            record.po_received_date = datetime.now()

    def button_validate(self):
        # overwrite this method set validation for (SFP) picking.
        for rec in self:
            stock_picking_rec = rec.search([
                ('group_id', '=', rec.group_id.id),
                ('id', '!=', rec.id),
                ('state', '!=', 'done'),
                ('location_id.barcode', 'not in', ['WH-QUALITY','WH-INPUT']),
            ])
            if stock_picking_rec and rec.picking_type_code != 'incoming' and rec.location_id.barcode == 'WH-POSTPRODUCTION':
                raise AccessError(_("Please complete the pending transfer before processing further"))
            mrp_production_rec = rec.env['mrp.production'].search([
                ('procurement_group_id', '=', rec.group_id.id),
                ('state', '!=', 'done'),
            ], limit=1)
            if not stock_picking_rec and mrp_production_rec and rec.picking_type_code != 'incoming' and rec.location_id.barcode == 'WH-POSTPRODUCTION':
                raise AccessError(_("Please complete the %s before processing further") % mrp_production_rec.name)
        return super().button_validate()

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
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        if res.picking_type_code == 'incoming':
            if 'skip_backorder' in self._context and self.env.context.get('button_validate_picking_ids'):
                picking_rec = self.sudo().search([
                    ('purchase_id', '=', self.purchase_id.id)
                ])
                if picking_rec and picking_rec[0].grn_sequence:
                    sequence = picking_rec[0].grn_sequence[:15]
                    number = str(len(picking_rec))
                    res.grn_sequence = str(sequence + '-' + number)
            else:
                sequence = self.env["ir.sequence"].next_by_code("stock.picking.grn")
                res.grn_sequence = str('GRN/' + self.get_fiscal_year_name() + '/' + sequence)
        return res



class QualityCheck(models.Model):
    _inherit = "quality.check"

    def do_pass(self):
        # overwrite this method set validation
        self.ensure_one()
        if not self.env.user.has_group('quality.group_quality_manager'):
            raise AccessError(_("You have no access rights pass quality check."))
        return super().do_pass()
