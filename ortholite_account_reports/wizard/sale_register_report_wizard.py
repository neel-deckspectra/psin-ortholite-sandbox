# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _

MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December'),
]

class SalesRegisterReportWizard(models.TransientModel):
    _name = 'sale.register.report.wizard'
    _description = "Sales Register Report Wizard"

    month = fields.Selection(MONTH_SELECTION, required=True, string='Month')
    year = fields.Selection(
        lambda self: [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 5)],
        string='Year',
        required=True,
        default=str(datetime.now().year),  # Set the default to current year
    )

    def get_month_label(self, value):
        # returns label for the month selection field.
        selection_dict = dict(self.fields_get()['month']['selection'])
        return selection_dict.get(value, '')

    def print_xls_report(self):
        account_move_line_obj = self.env['account.move.line']
        start_date = datetime(int(self.year), int(self.month), 1)
        last_day = calendar.monthrange(int(self.year), int(self.month))[1]
        end_date = datetime(int(self.year), int(self.month), last_day)
        account_move_line_rec = self.env['account.move.line'].sudo().search([
            ('move_id.state', '=', 'posted'),
            ('move_id.move_type', '=', 'out_invoice'),
            ('move_id.invoice_date', '>=', start_date.date()),
            ('move_id.invoice_date', '<=', end_date.date()),
            ('sale_line_ids', '!=', False),
        ], order='move_id asc')
        attributes_rec = account_move_line_rec.mapped('sale_line_ids.order_id').mapped('mrp_production_ids').mapped('bom_id').mapped('bom_line_ids').mapped('product_id').mapped('attribute_line_ids').mapped('attribute_id')
        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet('Sales Register', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet.write_merge(
            0, 1, 0, 28, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 28, '')
        worksheet.write_merge(
            3, 4, 0, 28, 'Sales Register', heading_format)
        worksheet.write_merge(5, 5, 0, 28, '')
        worksheet.write_merge(6, 7, 0, 28, str(self.get_month_label(self.month) + ' - ' + self.year), heading_format)
        worksheet.write_merge(8, 8, 0, 28, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(13 * 260)
        worksheet.col(2).width = int(35 * 260)
        worksheet.col(3).width = int(15 * 260)
        worksheet.col(4).width = int(13 * 260)
        worksheet.col(5).width = int(13 * 260)
        worksheet.col(6).width = int(13 * 260)
        worksheet.col(7).width = int(13 * 260)
        worksheet.col(8).width = int(13 * 260)
        worksheet.col(9).width = int(13 * 260)
        worksheet.col(10).width = int(13 * 260)
        worksheet.col(12).width = int(13 * 260)
        worksheet.col(13).width = int(13 * 260)
        worksheet.col(14).width = int(13 * 260)
        worksheet.col(16).width = int(13 * 260)
        worksheet.col(17).width = int(13 * 260)
        worksheet.col(18).width = int(13 * 260)
        worksheet.col(19).width = int(13 * 260)
        worksheet.col(20).width = int(13 * 260)
        worksheet.col(21).width = int(13 * 260)
        worksheet.col(22).width = int(13 * 260)
        worksheet.col(23).width = int(13 * 260)
        worksheet.col(24).width = int(13 * 260)
        worksheet.write(9, 0, "Number", bold_center_total)
        worksheet.write(9, 1, "Invoice Date", bold_center_total)
        worksheet.write(9, 2, "Customer", bold_center_total)
        worksheet.write(9, 3, "Brand", bold_center_total)
        worksheet.write(9, 4, "Product Category", bold_center_total)
        worksheet.write(9, 5, "Product", bold_center_total)
        worksheet.write(9, 6, "Company Currency", bold_center_total)
        worksheet.write(9, 7, "UoM", bold_center_total)
        worksheet.write(9, 8, "Quantity", bold_center_total)
        worksheet.write(9, 9, "Actual Qty", bold_center_total)
        worksheet.write(9, 10, "Unit Price", bold_center_total)
        worksheet.write(9, 11, "Tax excl.", bold_center_total)
        worksheet.write(9, 12, "Tax incl.", bold_center_total)
        worksheet.write(9, 13, "Untaxed Amount Signed", bold_center_total)
        worksheet.write(9, 14, "Order Reference", bold_center_total)
        worksheet.write(9, 15, "M O Number", bold_center_total)
        worksheet.write(9, 16, "RM Name", bold_center_total)
        worksheet.write(9, 17, "Category", bold_center_total)
        worksheet.write(9, 18, "Norms", bold_center_total)
        worksheet.write(9, 19, "Size", bold_center_total)
        worksheet.write(9, 20, "Per Unit Actual Landed Cost", bold_center_total)
        worksheet.write(9, 21, "Required Material Cost", bold_center_total)
        worksheet.write(9, 22, "Total Cost", bold_center_total)
        worksheet.write(9, 23, "Per Unit Standard Cost", bold_center_total)
        worksheet.write(9, 24, "Required Material Cost", bold_center_total)
        h_col = 25
        for attributes in attributes_rec:
            worksheet.write(9, h_col, attributes.name, bold_center_total)
            h_col += 1
        row = 10
        for line in account_move_line_rec:
            brand = ', '.join(map(lambda x: (x.name), line.move_id.brand_ids))
            mo_order = line.sale_line_ids[0].order_id.mrp_production_ids.filtered(lambda l: l.product_id.id == line.product_id.id)
            worksheet.write(row, 0, line.move_id.name or '', center)
            worksheet.write(row, 1, line.move_id.invoice_date.strftime('%m-%d-%Y'), center)
            worksheet.write(row, 2, line.move_id.partner_id.name or '', center)
            worksheet.write(row, 3, brand, center)
            worksheet.write(row, 4, line.product_categ_id.display_name or '', center)
            worksheet.write(row, 5, line.product_id.display_name or '', center)
            worksheet.write(row, 6, line.company_id.currency_id.name or '', center)
            worksheet.write(row, 7, line.product_uom_id.name or '', center)
            worksheet.write(row, 8, line.quantity, center_right)
            worksheet.write(row, 9, line.quantity, center_right)
            worksheet.write(row, 10, line.price_unit, center_right)
            worksheet.write(row, 11, line.price_subtotal, center_right)
            worksheet.write(row, 12, line.price_total, center_right)
            worksheet.write(row, 13, line.move_id.amount_untaxed_signed, center_right)
            worksheet.write(row, 14, line.sale_line_ids.mapped('order_id.name'), center)
            worksheet.write(row, 15, mo_order[0].name if mo_order else '', center)
            if mo_order and mo_order[0].bom_id:
                for bom_line in mo_order[0].bom_id.bom_line_ids:
                    worksheet.write(row, 16, bom_line.product_id.display_name or '', center)
                    worksheet.write(row, 17, bom_line.product_categ_id.name or '', center)
                    worksheet.write(row, 18, bom_line.product_qty or '', center_right)
                    worksheet.write(row, 19, '', center_right)
                    worksheet.write(row, 20, '', center_right)
                    worksheet.write(row, 21, '', center_right)
                    worksheet.write(row, 22, '', center_right)
                    worksheet.write(row, 23, bom_line.product_id.standard_price, center_right)
                    worksheet.write(row, 24, '', center_right)
                    col = 25
                    for attributes in attributes_rec:
                        attributes_values = ''
                        attributes_lines = bom_line.product_id.attribute_line_ids.filtered(lambda l: l.attribute_id.id == attributes.id)
                        if attributes_lines:
                            attributes_values = ', '.join(map(lambda x: (x.name), attributes_lines[0].value_ids))
                        worksheet.write(row, col, attributes_values, center)
                        col += 1
                    row += 1
            else:
                worksheet.write(row, 16, '', center_right)
                worksheet.write(row, 17, '', center_right)
                worksheet.write(row, 18, '', center_right)
                worksheet.write(row, 19, '', center_right)
                worksheet.write(row, 20, '', center_right)
                worksheet.write(row, 21, '', center_right)
                worksheet.write(row, 22, '', center_right)
                worksheet.write(row, 23, '', center_right)
                worksheet.write(row, 24, '', center_right)
                col = 25
                for attributes in attributes_rec:
                    attributes_values = ''
                    worksheet.write(row, col, attributes_values, center)
                    col += 1
                row += 1
            # row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('sales_register_report_' + self.get_month_label(self.month) + '_' + self.year + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "sale.register.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'sale.register.report.wizard'),
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