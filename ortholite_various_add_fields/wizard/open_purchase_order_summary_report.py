# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _

class OpenPurchaseOrderSummaryReportWizard(models.TransientModel):
    _name = 'open.purchase.order.summary.report.wizard'
    _description = "Open Purchase Order Summary Report Wizard"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    product_attribute_value_id = fields.Many2one(comodel_name='product.attribute.value', string="Brand")

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
        worksheet = workbook.add_sheet('Open Order Summary', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        start_date = self.start_date.strftime('%m-%d-%Y')
        end_date = self.end_date.strftime('%m-%d-%Y')
        worksheet.write_merge(
            0, 1, 0, 13, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 13, '')
        worksheet.write_merge(
            3, 4, 0, 13, 'Open Order Summary', heading_format)
        worksheet.write_merge(5, 5, 0, 13, '')
        worksheet.write_merge(
            6, 7, 0, 13, ('Start Date: %s End Date: %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 13, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(15 * 260)
        worksheet.col(2).width = int(20 * 260)
        worksheet.col(3).width = int(20 * 260)
        worksheet.col(4).width = int(40 * 260)
        worksheet.col(5).width = int(15 * 260)
        worksheet.col(6).width = int(25 * 260)
        worksheet.col(7).width = int(10 * 260)
        worksheet.col(8).width = int(20 * 260)
        worksheet.col(9).width = int(10 * 260)
        worksheet.col(10).width = int(15 * 260)
        worksheet.col(11).width = int(15 * 260)
        worksheet.col(12).width = int(10 * 260)
        worksheet.col(13).width = int(22 * 260)
        worksheet.write(9, 0, "PO #", bold_center_total)
        worksheet.write(9, 1, "PO Date", bold_center_total)
        worksheet.write(9, 2, "Expected Arrival", bold_center_total)
        worksheet.write(9, 3, "PO Ageing Days", bold_center_total)
        worksheet.write(9, 4, "Product Name", bold_center_total)
        worksheet.write(9, 5, "Item Code", bold_center_total)
        worksheet.write(9, 6, "Vendor", bold_center_total)
        worksheet.write(9, 7, "UoM", bold_center_total)
        worksheet.write(9, 8, "Category", bold_center_total)
        worksheet.write(9, 9, "Price", bold_center_total)
        worksheet.write(9, 10, "Value", bold_center_total)
        worksheet.write(9, 11, "Thick", bold_center_total)
        worksheet.write(9, 12, "PO Quantity", bold_center_total)
        worksheet.write(9, 13, "Total Thickness/Pairs", bold_center_total)
        purchase_order_line_obj = self.env['purchase.order.line']
        category_obj = self.env['product.category']
        attribute_obj = self.env['product.attribute']
        if self.product_attribute_value_id:
            purchase_order_line_rec = purchase_order_line_obj.sudo().search([
                ('state', '=', 'purchase'),
                ('order_id.date_approve', '>=', self.start_date),
                ('order_id.date_approve', '<=', self.end_date),
                ('product_attribute_value_id', '=', self.product_attribute_value_id.id),
            ], order='order_id asc')
        else:
            purchase_order_line_rec = purchase_order_line_obj.sudo().search([
                ('state', '=', 'purchase'),
                ('order_id.date_approve', '>=', self.start_date),
                ('order_id.date_approve', '<=', self.end_date),
            ], order='order_id asc')
        row = 10
        for line in purchase_order_line_rec:
            category_rec = category_obj.sudo().search([
                ('name', '=', 'Uncovered Flat Sheet')
            ], limit=1)
            date_planned = ''
            ageing_days = ''
            if line.order_id.date_planned:
                date_planned = line.order_id.date_planned.strftime('%d-%m-%Y')
                ageing_days = (line.order_id.date_planned.date() - fields.Date.today()).days
            worksheet.write(row, 0, line.order_id.name, center)
            worksheet.write(row, 1, line.order_id.date_approve.strftime('%d-%m-%Y'), center)
            worksheet.write(row, 2, date_planned, center)
            worksheet.write(row, 3, ageing_days, center_right)
            worksheet.write(row, 4, line.product_template_id.name or '', center)
            worksheet.write(row, 5, line.product_template_id.default_code or '', center)
            worksheet.write(row, 6, line.order_id.partner_id.name or '', center)
            worksheet.write(row, 7, line.product_uom.name or '', center)
            worksheet.write(row, 8, line.product_template_id.categ_id.name or '', center)
            worksheet.write(row, 9, line.price_unit, center_right)
            worksheet.write(row, 10, line.price_subtotal, center_right)
            worksheet.write(row, 11, '', center)
            worksheet.write(row, 12, line.product_qty, center_right)
            worksheet.write(row, 13, '', center)
            if category_rec and line.product_template_id.categ_id.id == category_rec.id:
                attribute_rec = attribute_obj.sudo().search([
                    ('name', '=', 'Thickness')
                ], limit=1)
                if attribute_rec:
                    attribute_line = line.product_template_id.attribute_line_ids.filtered(
                        lambda line: line.attribute_id.id == attribute_rec.id)
                    if attribute_line and attribute_line[0].value_ids:
                        worksheet.write(row, 11, attribute_line[0].value_ids[0].float_value, center_right)
                        worksheet.write(row, 13, attribute_line[0].value_ids[0].float_value * line.product_qty, center_right)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('open_order_summary_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "open.purchase.order.summary.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'open.purchase.order.summary.report.wizard'),
            ('type', '=', 'binary')
        ],limit=1)
        if attachment:
            attachment.write(attachment_vals)
        else:
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