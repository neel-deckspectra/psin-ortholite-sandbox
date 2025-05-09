# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _

class SalesForecastExcelReportWizard(models.TransientModel):
    _name = 'sales.forecast.excel.report.wizard'
    _description = "Sales Forecast Excel Report Wizard"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    category_id = fields.Many2one("product.category", string="Product Category")
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
        worksheet = workbook.add_sheet('Forecast Summary', bold_center)
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
        month_list = []
        current_date = self.start_date
        while current_date <= self.end_date:
            month_list.append(current_date.strftime('%B %Y'))
            current_date += relativedelta(months=1)
        worksheet.write_merge(
            0, 1, 0, 16, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 16, '')
        worksheet.write_merge(
            3, 4, 0, 16, 'Forecast Summary', heading_format)
        worksheet.write_merge(5, 5, 0, 16, '')
        worksheet.write_merge(
            6, 7, 0, 16, ('Start Date : %s End Date : %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 16, '')
        worksheet.col(0).width = int(10 * 260)
        worksheet.col(1).width = int(15 * 260)
        worksheet.col(4).width = int(10 * 260)
        worksheet.col(5).width = int(20 * 260)
        worksheet.col(6).width = int(20 * 260)
        worksheet.col(7).width = int(25 * 260)
        worksheet.col(8).width = int(15 * 260)
        worksheet.col(10).width = int(20 * 260)
        worksheet.col(12).width = int(22 * 260)
        worksheet.col(13).width = int(20 * 260)
        worksheet.col(14).width = int(20 * 260)
        worksheet.col(16).width = int(20 * 260)
        worksheet.write(9, 0, "Sr.No", bold_center_total)
        worksheet.write(9, 1, "Month-Year", bold_center_total)
        worksheet.write(9, 2, "Season", bold_center_total)
        worksheet.write(9, 3, "Brand", bold_center_total)
        worksheet.write(9, 4, "FC Type", bold_center_total)
        worksheet.write(9, 5, "Customer Code", bold_center_total)
        worksheet.write(9, 6, "Customer Name", bold_center_total)
        worksheet.write(9, 7, "Customer Service Name", bold_center_total)
        worksheet.write(9, 8, "Category Type", bold_center_total)
        worksheet.write(9, 9, "Item Code", bold_center_total)
        worksheet.write(9, 10, "Item Description", bold_center_total)
        worksheet.write(9, 11, "Foam Type", bold_center_total)
        worksheet.write(9, 12, "Forecasted Quantity", bold_center_total)
        worksheet.write(9, 13, "OIH Quantity", bold_center_total)
        worksheet.write(9, 14, "Balance Quantity", bold_center_total)
        worksheet.write(9, 15, "Per Price", bold_center_total)
        worksheet.write(9, 16, "Total Value", bold_center_total)
        crm_line_opportunity_obj = self.env['crm.lead.line']
        if self.product_attribute_value_id and self.category_id:
            crm_opportunity_rec = crm_line_opportunity_obj.sudo().search([
                ('lead_id.type', '=', 'opportunity'),
                ('fc_date', '>=', self.start_date),
                ('fc_date', '<=', self.end_date),
                ('product_attribute_value_id', '=', self.product_attribute_value_id.id),
                ('category_id', '=', self.category_id.id),
            ], order='fc_date asc')
        elif self.product_attribute_value_id and not self.category_id:
            crm_opportunity_rec = crm_line_opportunity_obj.sudo().search([
                ('lead_id.type', '=', 'opportunity'),
                ('fc_date', '>=', self.start_date),
                ('fc_date', '<=', self.end_date),
                ('product_attribute_value_id', '=', self.product_attribute_value_id.id),
            ], order='fc_date asc')
        elif not self.product_attribute_value_id and self.category_id:
            crm_opportunity_rec = crm_line_opportunity_obj.sudo().search([
                ('lead_id.type', '=', 'opportunity'),
                ('fc_date', '>=', self.start_date),
                ('fc_date', '<=', self.end_date),
                ('category_id', '=', self.category_id.id),
            ], order='fc_date asc')
        else:
            crm_opportunity_rec = crm_line_opportunity_obj.sudo().search([
                ('lead_id.type', '=', 'opportunity'),
                ('fc_date', '>=', self.start_date),
                ('fc_date', '<=', self.end_date),
            ], order='fc_date asc')
        row = 10
        sr_no = 1
        for line in crm_opportunity_rec:
            worksheet.write(row, 0, sr_no, center_right)
            worksheet.write(row, 1, str(line.fc_date.strftime('%B %Y')), center)
            worksheet.write(row, 2, line.lead_id.season_id.name or '', center)
            worksheet.write(row, 3, line.product_attribute_value_id.name or '', center)
            fc_type = ''
            if line.lead_id.fc_type:
                fc_type = 'Buy Plan'
                if line.lead_id.fc_type == 'domestic':
                    fc_type = 'Domestic'
            worksheet.write(row, 4, fc_type, center)
            worksheet.write(row, 5, line.lead_id.partner_id.code or '', center)
            worksheet.write(row, 6, line.lead_id.partner_id.name or '', center)
            worksheet.write(row, 7, line.lead_id.customer_group_id.name or '', center)
            worksheet.write(row, 8, line.category_id.name or '', center)
            worksheet.write(row, 9, line.product_id.default_code or '', center)
            worksheet.write(row, 10, line.product_id.display_name or '', center)
            worksheet.write(row, 11, line.uom_id.name, center)
            worksheet.write(row, 12, line.product_qty, center_right)
            worksheet.write(row, 13, line.order_qty, center_right)
            worksheet.write(row, 14, (line.product_qty - line.order_qty), center_right)
            worksheet.write(row, 15, line.price_unit, center_right)
            worksheet.write(row, 16, '0.0', center_right)
            row += 1
            sr_no += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('forecast_summary_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "sales.forecast.excel.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'sales.forecast.excel.report.wizard'),
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