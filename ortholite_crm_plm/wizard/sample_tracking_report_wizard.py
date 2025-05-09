# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _
from odoo.tools import html2plaintext

class SampleTrackingReportWizard(models.TransientModel):
    _name = 'sample.tracking.report.wizard'
    _description = "Sample Tracking Report Wizard"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            # Ensure end_date is greater than start_date
            if record.end_date < record.start_date:
                raise ValidationError("End date must be greater than the start date.")

    def add_days_excluding_sundays(self, date):
        planned_date = date
        days_to_add = 4
        while days_to_add > 0:
            planned_date += timedelta(days=1)
            if planned_date.weekday() != 6:
                days_to_add -= 1
        return planned_date

    def print_xls_report(self):
        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet('Sample Tracking', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet.write_merge(
            0, 1, 0, 18, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 18, '')
        worksheet.write_merge(
            3, 4, 0, 18, 'Sample Tracking', heading_format)
        worksheet.write_merge(5, 5, 0, 18, '')
        start_date = self.start_date.strftime('%m-%d-%Y')
        end_date = self.end_date.strftime('%m-%d-%Y')
        worksheet.write_merge(6, 7, 0, 18, ('Start Date : %s End Date : %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 18, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(15 * 260)
        worksheet.col(2).width = int(15 * 260)
        worksheet.col(3).width = int(30 * 260)
        worksheet.col(4).width = int(20 * 260)
        worksheet.col(5).width = int(10 * 260)
        worksheet.col(6).width = int(20 * 260)
        worksheet.col(7).width = int(30 * 260)
        worksheet.col(8).width = int(15 * 260)
        worksheet.col(9).width = int(10 * 260)
        worksheet.col(10).width = int(15 * 260)
        worksheet.col(11).width = int(15 * 260)
        worksheet.col(12).width = int(15 * 260)
        worksheet.col(13).width = int(15 * 260)
        worksheet.col(14).width = int(15 * 260)
        worksheet.col(15).width = int(25 * 260)
        worksheet.col(16).width = int(15 * 260)
        worksheet.col(17).width = int(15 * 260)
        worksheet.col(18).width = int(20 * 260)
        worksheet.write(9, 0, "REQ", bold_center_total)
        worksheet.write(9, 1, "Sample Type", bold_center_total)
        worksheet.write(9, 2, "Customer", bold_center_total)
        worksheet.write(9, 3, "Product Category", bold_center_total)
        worksheet.write(9, 4, "Size", bold_center_total)
        worksheet.write(9, 5, "Pairs / Sheet Shipped Quantity", bold_center_total)
        worksheet.write(9, 6, "Item Description", bold_center_total)
        worksheet.write(9, 7, "Brand", bold_center_total)
        worksheet.write(9, 8, "Mail Date", bold_center_total)
        worksheet.write(9, 9, "Status", bold_center_total)
        worksheet.write(9, 10, "Planned EX FAC", bold_center_total)
        worksheet.write(9, 11, "Actual EX FAC", bold_center_total)
        worksheet.write(9, 12, "Month", bold_center_total)
        worksheet.write(9, 13, "Week No", bold_center_total)
        worksheet.write(9, 14, "Feedback", bold_center_total)
        worksheet.write(9, 15, "Remarks", bold_center_total)
        worksheet.write(9, 16, "OTDP", bold_center_total)
        worksheet.write(9, 17, "Shipped", bold_center_total)
        worksheet.write(9, 18, "Balance To Ship", bold_center_total)
        mrp_eco_rec = self.env['mrp.eco'].sudo().search([
            ('create_date', '>=', self.start_date),
            ('create_date', '<=', self.end_date),
        ], order='id asc')
        row = 10
        for eco in mrp_eco_rec:
            planned_date = self.add_days_excluding_sundays(eco.create_date.date())
            note = ''
            brand = ''
            product_category = ''
            if eco.note:
                note = html2plaintext(eco.note)
            if eco.tag_ids:
                brand = ', '.join(map(lambda x: (x.name), eco.tag_ids))
            if eco.product_category_ids:
                product_category = ', '.join(map(lambda x: (x.name), eco.product_category_ids))
            otdp = 'Not on time'
            if eco.dispatched_date and eco.dispatched_date <= planned_date:
                otdp = 'On time'
            worksheet.write(row, 0, eco.user_id.name or '', center)
            worksheet.write(row, 1, eco.type_id.name, center)
            worksheet.write(row, 2, eco.contact_id.name or '', center)
            worksheet.write(row, 3, product_category, center)
            worksheet.write(row, 4, eco.size or '', center)
            worksheet.write(row, 5, eco.quantity, center_right)
            worksheet.write(row, 6, eco.display_name or '', center)
            worksheet.write(row, 7, brand, center)
            worksheet.write(row, 8, eco.create_date.strftime('%d-%m-%Y'), center)
            worksheet.write(row, 9, eco.status or '', center)
            worksheet.write(row, 10, planned_date.strftime('%d-%m-%Y'), center)
            worksheet.write(row, 11, eco.dispatched_date.strftime('%d-%m-%Y') if eco.dispatched_date else '', center)
            worksheet.write(row, 12, eco.create_date.strftime('%B'), center)
            worksheet.write(row, 13, eco.create_date.strftime('%V'), center_right)
            worksheet.write(row, 14, eco.feedback or '', center)
            worksheet.write(row, 15, note, center)
            worksheet.write(row, 16, otdp, center)
            worksheet.write(row, 17, eco.shipped, center_right)
            worksheet.write(row, 18, eco.quantity - eco.shipped, center_right)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('sample_tracking_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "sample.tracking.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'sample.tracking.report.wizard'),
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