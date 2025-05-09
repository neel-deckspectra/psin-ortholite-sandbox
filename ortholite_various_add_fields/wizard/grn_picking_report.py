# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _

class GRNReportWizard(models.TransientModel):
    _name = 'grn.picking.report.wizard'
    _description = "GRN Report Wizard"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category')
    partner_id = fields.Many2one('res.partner', string='Vendor')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            # Ensure end_date is greater than start_date
            if record.end_date < record.start_date:
                raise ValidationError("End date must be greater than the start date.")

    def print_xls_report(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet('GRN', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        start_date = self.start_date.strftime('%m-%d-%Y')
        end_date = self.end_date.strftime('%m-%d-%Y')
        worksheet.write_merge(
            0, 1, 0, 16, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 16, '')
        worksheet.write_merge(
            3, 4, 0, 16, 'GRN', heading_format)
        worksheet.write_merge(5, 5, 0, 16, '')
        worksheet.write_merge(
            6, 7, 0, 16, ('Start Date: %s End Date: %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 13, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(18 * 260)
        worksheet.col(2).width = int(20 * 260)
        worksheet.col(3).width = int(20 * 260)
        worksheet.col(4).width = int(40 * 260)
        worksheet.col(5).width = int(20 * 260)
        worksheet.col(6).width = int(15 * 260)
        worksheet.col(7).width = int(25 * 260)
        worksheet.col(8).width = int(18 * 260)
        worksheet.col(9).width = int(10 * 260)
        worksheet.col(10).width = int(15 * 260)
        worksheet.col(11).width = int(15 * 260)
        worksheet.col(12).width = int(15 * 260)
        worksheet.col(13).width = int(15 * 260)
        worksheet.col(14).width = int(15 * 260)
        worksheet.col(15).width = int(20 * 260)
        worksheet.col(16).width = int(20 * 260)
        worksheet.write(9, 0, "GRN Number", bold_center_total)
        worksheet.write(9, 1, "PO Received Date", bold_center_total)
        worksheet.write(9, 2, "Lot Serial Number", bold_center_total)
        worksheet.write(9, 3, "Invoice Date", bold_center_total)
        worksheet.write(9, 4, "Vendor Name", bold_center_total)
        worksheet.write(9, 5, "Product Category", bold_center_total)
        worksheet.write(9, 6, "Item Code", bold_center_total)
        worksheet.write(9, 7, "Product", bold_center_total)
        worksheet.write(9, 8, "Unit of Measure", bold_center_total)
        worksheet.write(9, 9, "Location", bold_center_total)
        worksheet.write(9, 10, "PO Number", bold_center_total)
        worksheet.write(9, 11, "Quantity", bold_center_total)
        worksheet.write(9, 12, "Received Qty", bold_center_total)
        worksheet.write(9, 13, "Unit Price", bold_center_total)
        worksheet.write(9, 14, "Currency", bold_center_total)
        worksheet.write(9, 15, "Received Value", bold_center_total)
        worksheet.write(9, 16, "Currency Con Value", bold_center_total)
        stock_move_obj = self.env['stock.move']
        if self.product_categ_id and self.partner_id:
            stock_move_rec = stock_move_obj.sudo().search([
                ('picking_id.po_received_date', '!=', False),
                ('purchase_line_id', '!=', False),
                ('picking_id.po_received_date', '>=', self.start_date),
                ('picking_id.po_received_date', '<=', self.end_date),
                ('product_categ_id', '=', self.product_categ_id.id),
                ('picking_id.partner_id', '=', self.partner_id.id),
                ('picking_id.picking_type_code', '=', 'incoming'),
            ], order='picking_id asc')
        elif self.product_categ_id and not self.partner_id:
            stock_move_rec = stock_move_obj.sudo().search([
                ('picking_id.po_received_date', '!=', False),
                ('purchase_line_id', '!=', False),
                ('picking_id.po_received_date', '>=', self.start_date),
                ('picking_id.po_received_date', '<=', self.end_date),
                ('product_categ_id', '=', self.product_categ_id.id),
                ('picking_id.picking_type_code', '=', 'incoming'),
            ], order='picking_id asc')
        elif not self.product_categ_id and self.partner_id:
            stock_move_rec = stock_move_obj.sudo().search([
                ('picking_id.po_received_date', '!=', False),
                ('purchase_line_id', '!=', False),
                ('picking_id.po_received_date', '>=', self.start_date),
                ('picking_id.po_received_date', '<=', self.end_date),
                ('picking_id.picking_type_code', '=', 'incoming'),
                ('picking_id.partner_id', '=', self.partner_id.id),
            ], order='picking_id asc')
        else:
            stock_move_rec = stock_move_obj.sudo().search([
                ('picking_id.po_received_date', '!=', False),
                ('purchase_line_id', '!=', False),
                ('picking_id.po_received_date', '>=', self.start_date),
                ('picking_id.po_received_date', '<=', self.end_date),
                ('picking_id.picking_type_code', '=', 'incoming'),
            ], order='picking_id asc')
        row = 10
        for line in stock_move_rec:
            sr_number = ''
            invoice_date = ''
            total_value = 0.0
            amount = 0.0
            move_line = line.move_line_ids.filtered(
                lambda move_line: move_line.move_id.id == line.id)
            if move_line:
                line_sr_number = move_line[0].lot_id
                if line_sr_number:
                    sr_number = move_line[0].lot_id.display_name
                line_invoice_date = move_line[0].invoice_date
                if line_invoice_date:
                    invoice_date = move_line[0].invoice_date.strftime('%d-%m-%Y')
            inr_currency = self.env.ref('base.INR')
            total_value = (line.product_uom_qty * line.price_unit)
            date = line.picking_id.po_received_date.date() or fields.Date.context_today(line)
            from_currency = line.purchase_line_id.currency_id or line.company_id.currency_id
            amount = from_currency._convert(total_value, inr_currency, line.company_id, date)
            worksheet.write(row, 0, line.picking_id.grn_sequence or '', center)
            worksheet.write(row, 1, line.picking_id.po_received_date.strftime('%d-%m-%Y'), center)
            worksheet.write(row, 2, sr_number, center)
            worksheet.write(row, 3, invoice_date, center)
            worksheet.write(row, 4, line.picking_id.partner_id.display_name or '', center)
            worksheet.write(row, 5, line.product_categ_id.display_name or '', center)
            worksheet.write(row, 6, line.product_id.default_code or '', center)
            worksheet.write(row, 7, line.product_id.display_name or '', center)
            worksheet.write(row, 8, line.product_uom.display_name or '', center)
            worksheet.write(row, 9, line.picking_id.location_dest_id.display_name or '', center)
            worksheet.write(row, 10, line.picking_id.origin or '', center)
            worksheet.write(row, 11, line.quantity, center_right)
            worksheet.write(row, 12, line.product_uom_qty, center_right)
            worksheet.write(row, 13, line.price_unit, center_right)
            worksheet.write(row, 14, line.purchase_line_id.currency_id.display_name or '', center)
            worksheet.write(row, 15, total_value, center_right)
            worksheet.write(row, 16, amount, center_right)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('grn_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "grn.picking.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'grn.picking.report.wizard'),
            ('type', '=', 'binary')
        ])
        if attachment:
            attachment.unlink()
        attachment = IrAttachment.create(attachment_vals)
        # TODO: make user error here
        if not attachment:
            raise UserError(_('There is no attachments...'))
        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }