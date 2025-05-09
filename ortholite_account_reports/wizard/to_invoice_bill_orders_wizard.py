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

class ToInvoiceBillOrdersReportWizard(models.TransientModel):
    _name = 'to.invoice.bill.orders.report.wizard'
    _description = "To Invoice/Bill Orders Report Wizard"

    month = fields.Selection(MONTH_SELECTION, required=True, string='Month')
    year = fields.Selection(
        lambda self: [(str(year), str(year)) for year in range(datetime.now().year - 5, datetime.now().year + 5)],
        string='Year',
        required=True,
        default=str(datetime.now().year),  # Set the default to current year
    )
    type = fields.Selection([
        ('receivables', 'Receivables'),
        ('payables', 'Payables'),
    ], string='Type', required=True, default='receivables')

    def get_month_label(self, value):
        # returns label for the month selection field.
        selection_dict = dict(self.fields_get()['month']['selection'])
        return selection_dict.get(value, '')

    def print_xls_report(self):
        start_date = datetime(int(self.year), int(self.month), 1)
        last_day = calendar.monthrange(int(self.year), int(self.month))[1]
        end_date = datetime(int(self.year), int(self.month), last_day)
        if self.type == 'receivables':
            to_invoice_bill_orders_rec = self.env['sale.order'].sudo().search([
                ('invoice_status', '=', 'to invoice'),
                ('date_order', '>=', start_date.date()),
                ('date_order', '<=', end_date.date()),
            ], order='date_order asc')
        else:
            to_invoice_bill_orders_rec = self.env['purchase.order'].sudo().search([
                ('invoice_status', '=', 'to invoice'),
                ('date_order', '>=', start_date.date()),
                ('date_order', '<=', end_date.date()),
            ], order='date_order asc')
        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet('To Invoice/Bill Orders', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet.write_merge(
            0, 1, 0, 5, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 5, '')
        worksheet.write_merge(
            3, 4, 0, 5, 'To Invoice/Bill Orders', heading_format)
        worksheet.write_merge(5, 5, 0, 5, '')
        worksheet.write_merge(6, 7, 0, 5, str(self.get_month_label(self.month) + ' - ' + self.year), heading_format)
        worksheet.write_merge(8, 8, 0, 5, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(45 * 260)
        worksheet.col(2).width = int(15 * 260)
        worksheet.col(3).width = int(25 * 260)
        worksheet.col(4).width = int(20 * 260)
        worksheet.col(5).width = int(30 * 260)
        worksheet.write(9, 0, "Number", bold_center_total)
        if self.type == 'receivables':
            worksheet.write(9, 1, "Customer", bold_center_total)    
        else:
            worksheet.write(9, 1, "Vendor", bold_center_total)
        worksheet.write(9, 2, "Order Date", bold_center_total)
        worksheet.write(9, 3, "Payment Terms", bold_center_total)
        worksheet.write(9, 4, "Total Amount", bold_center_total)
        worksheet.write(9, 5, "Responsible Person", bold_center_total)
        row = 10
        for line in to_invoice_bill_orders_rec:
            worksheet.write(row, 0, line.display_name or '', center)
            worksheet.write(row, 1, line.partner_id.name or '', center)
            worksheet.write(row, 2, line.date_order.strftime('%d-%m-%Y'), center)
            worksheet.write(row, 3, line.payment_term_id.name or '', center)
            worksheet.write(row, 4, line.amount_untaxed, center_right)
            worksheet.write(row, 5, line.user_id.name or '', center)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('to_invoice_bill_orders_report_' + self.get_month_label(self.month) + '_' + self.year + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "to.invoice.bill.orders.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'to.invoice.bill.orders.report.wizard'),
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