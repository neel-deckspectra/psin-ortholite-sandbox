# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _

class ActivityTrackingExcelReportWizard(models.TransientModel):
    _name = 'activity.tracking.excel.report.wizard'
    _description = "Activity Tracking Excel Report Wizard"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    activity_user_id = fields.Many2one("res.users", string="Salesperson")
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
        worksheet = workbook.add_sheet('Activity Tracking', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        start_date = self.start_date.strftime('%m-%d-%Y')
        end_date = self.end_date.strftime('%m-%d-%Y')
        worksheet.write_merge(
            0, 1, 0, 8, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 8, '')
        worksheet.write_merge(
            3, 4, 0, 8, 'Activity Tracking', heading_format)
        worksheet.write_merge(5, 5, 0, 8, '')
        worksheet.write_merge(
            6, 7, 0, 8, ('Start Date : %s End Date : %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 8, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(40 * 260)
        worksheet.col(2).width = int(15 * 260)
        worksheet.col(3).width = int(30 * 260)
        worksheet.col(4).width = int(30 * 260)
        worksheet.col(5).width = int(30 * 260)
        worksheet.col(6).width = int(30 * 260)
        worksheet.col(7).width = int(30 * 260)
        worksheet.col(8).width = int(30 * 260)
        worksheet.write(9, 0, "Date", bold_center_total)
        worksheet.write(9, 1, "Customer", bold_center_total)
        worksheet.write(9, 2, "Brand", bold_center_total)
        worksheet.write(9, 3, "Purpose of Visit", bold_center_total)
        worksheet.write(9, 4, "Factory Contact", bold_center_total)
        worksheet.write(9, 5, "Ortholite Grades Used", bold_center_total)
        worksheet.write(9, 6, "Competitor Info", bold_center_total)
        worksheet.write(9, 7, "Volume/Season", bold_center_total)
        worksheet.write(9, 8, "Remarks", bold_center_total)
        mail_activity_obj = self.env['mail.activity']
        if self.product_attribute_value_id and self.activity_user_id:
            mail_activity_rec = mail_activity_obj.sudo().with_context(active_test=False).search([
                ('is_visit', '=', True),
                ('res_model', '=', 'res.partner'),
                ('date_deadline', '>=', self.start_date),
                ('date_deadline', '<=', self.end_date),
                ('product_attribute_value_id', '=', self.product_attribute_value_id.id),
                ('user_id', '=', self.activity_user_id.id),
            ])
        elif self.product_attribute_value_id and not self.activity_user_id:
            mail_activity_rec = mail_activity_obj.sudo().with_context(active_test=False).search([
                ('is_visit', '=', True),
                ('res_model', '=', 'res.partner'),
                ('date_deadline', '>=', self.start_date),
                ('date_deadline', '<=', self.end_date),
                ('product_attribute_value_id', '=', self.product_attribute_value_id.id),
            ])
        elif not self.product_attribute_value_id and self.activity_user_id:
            mail_activity_rec = mail_activity_obj.sudo().with_context(active_test=False).search([
                ('is_visit', '=', True),
                ('res_model', '=', 'res.partner'),
                ('date_deadline', '>=', self.start_date),
                ('date_deadline', '<=', self.end_date),
                ('user_id', '=', self.activity_user_id.id),
            ])
        else:
            mail_activity_rec = mail_activity_obj.sudo().with_context(active_test=False).search([
                ('is_visit', '=', True),
                ('res_model', '=', 'res.partner'),
                ('date_deadline', '>=', self.start_date),
                ('date_deadline', '<=', self.end_date),
            ])
        row = 10
        partner_obj = self.env['res.partner']
        for line in mail_activity_rec:
            partner_rec = partner_obj.sudo().browse(line.res_id)
            worksheet.write(row, 0, str(line.date_deadline.strftime('%m-%d-%Y')), center_right)
            worksheet.write(row, 1, partner_rec.name or '', center)
            worksheet.write(row, 2, line.product_attribute_value_id.name or '', center)
            worksheet.write(row, 3, line.purpose_of_visit or '', center)
            worksheet.write(row, 4, line.factory_contact or '', center)
            worksheet.write(row, 5, line.grades_used or '', center)
            worksheet.write(row, 6, line.competitor_info or '', center)
            worksheet.write(row, 7, line.season_id.name or '', center)
            worksheet.write(row, 8, line.remarks or '', center)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('activity_tracking_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "activity.tracking.excel.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'activity.tracking.excel.report.wizard'),
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