
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import xlwt
import io
import base64
from odoo import api, fields, models, _

class PurchaseRegisterReportWizard(models.TransientModel):
    _name = 'purchase.register.report.wizard'
    _description = "Purchase Register Report Wizard"

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    product_categ_id = fields.Many2one('product.category',string='Product Category')

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
        worksheet = workbook.add_sheet('Purchase Register', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        start_date = self.start_date.strftime('%m-%d-%Y')
        end_date = self.end_date.strftime('%m-%d-%Y')
        worksheet.write_merge(
            0, 1, 0, 26, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 26, '')
        worksheet.write_merge(
            3, 4, 0, 26, 'Purchase Register', heading_format)
        worksheet.write_merge(5, 5, 0, 26, '')
        worksheet.write_merge(
            6, 7, 0, 26, ('Start Date: %s End Date: %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 26, '')
        worksheet.col(0).width = int(15 * 260)
        worksheet.col(1).width = int(13 * 260)
        worksheet.col(2).width = int(35 * 260)
        worksheet.col(3).width = int(35 * 260)
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
        worksheet.col(25).width = int(13 * 260)
        worksheet.write(9, 0, "Supplier Invoice No", bold_center_total)
        worksheet.write(9, 1, "Invoice Date", bold_center_total)
        worksheet.write(9, 2, "Supplier Name", bold_center_total)
        worksheet.write(9, 3, "Description & HSN Code", bold_center_total)
        worksheet.write(9, 4, "Product Category", bold_center_total)
        worksheet.write(9, 5, "Quantity", bold_center_total)
        worksheet.write(9, 6, "AmtFCr/Unit", bold_center_total)
        worksheet.write(9, 7, "Cost USD", bold_center_total)
        worksheet.write(9, 8, "Company Currency", bold_center_total)
        worksheet.write(9, 9, "Duty/BCD INR", bold_center_total)
        worksheet.write(9, 10, "Advance License Number", bold_center_total)
        worksheet.write(9, 11, "Total Freight", bold_center_total)
        worksheet.write(9, 12, "Total Landed Cost", bold_center_total)
        worksheet.write(9, 13, "Per MM Cost INR", bold_center_total)
        worksheet.write(9, 14, "Freight", bold_center_total)
        worksheet.write(9, 15, "Insurance", bold_center_total)
        worksheet.write(9, 16, "Clearingcharge", bold_center_total)
        worksheet.write(9, 17, "Liner Charges", bold_center_total)
        worksheet.write(9, 18, "AAI Charges", bold_center_total)
        worksheet.write(9, 19, "CFS Charges", bold_center_total)
        worksheet.write(9, 20, "Inland Transport", bold_center_total)
        worksheet.write(9, 21, "Fine AMT", bold_center_total)
        worksheet.write(9, 22, "Int Charges", bold_center_total)
        worksheet.write(9, 23, "IGST", bold_center_total)
        worksheet.write(9, 24, "Wght (Kg)", bold_center_total)
        worksheet.write(9, 25, "Exch Rate", bold_center_total)
        worksheet.write(9, 26, "Qty(InMM)", bold_center_total)
        account_move_line_obj = self.env['account.move.line']
        categorie_rec = self.env['product.category'].sudo().search([
            ('name', 'in', ['Uncovered Flat Sheet', 'Adhesives', 'Logo', 'Fabric'])
        ])
        if self.product_categ_id:
            account_move_line_rec = account_move_line_obj.sudo().search([
                ('move_id.state', '=', 'posted'),
                ('move_id.move_type', '=', 'in_invoice'),
                ('move_id.invoice_date', '>=', self.start_date),
                ('move_id.invoice_date', '<=', self.end_date),
                ('product_categ_id', '=', self.product_categ_id.id),
                ('product_id', '!=', False),
                ('product_id.detailed_type', '=', 'product'),
                ('product_id.categ_id', 'in', categorie_rec.ids),
            ], order='move_id asc')
        else:
            account_move_line_rec = account_move_line_obj.sudo().search([
                ('move_id.state', '=', 'posted'),
                ('move_id.move_type', '=', 'in_invoice'),
                ('move_id.invoice_date', '>=', self.start_date),
                ('move_id.invoice_date', '<=', self.end_date),
                ('product_id', '!=', False),
                ('product_id.detailed_type', '=', 'product'),
                ('product_id.categ_id', 'in', categorie_rec.ids),
            ], order='move_id asc')
        row = 10
        usd_currency_id = self.env['res.currency'].sudo().browse(self.env.ref("base.USD").id)
        currency_rate_obj = self.env['res.currency.rate']
        attribute_obj = self.env['product.attribute']
        for line in account_move_line_rec:
            currency_rate_rec = currency_rate_obj.sudo().search([
                ('currency_id', '=', usd_currency_id.id),
                ('name', '<=', line.move_id.invoice_date),
            ], order='name desc', limit=1)
            cost_usd = line.quantity * currency_rate_rec.company_rate
            igst = ', '.join(map(lambda x: (x.invoice_label or x.name), line.tax_ids))
            total_sum_line = (line.freight, line.insurance, line.clearingcharge, line.liner_charges,
                line.aai_charges, line.cfs_charges, line.inland_transport, line.fine_amt, line.int_charges)
            total_freight = sum(total_sum_line)
            company_currency = round(cost_usd * currency_rate_rec.inverse_company_rate, 2)
            landed_cost_line = (company_currency, line.duty_bcd_inr, total_freight)
            total_landed_cost = sum(landed_cost_line)
            worksheet.write(row, 0, line.move_id.ref or '', center)
            worksheet.write(row, 1, line.move_id.invoice_date.strftime('%m-%d-%Y'), center)
            worksheet.write(row, 2, line.move_id.partner_id.name or '', center)
            worksheet.write(row, 3, line.product_id.display_name or '', center)
            worksheet.write(row, 4, line.product_id.categ_id.display_name or '', center)
            worksheet.write(row, 5, line.quantity, center_right)
            worksheet.write(row, 6, round(currency_rate_rec.company_rate, 2) or '', center_right)
            worksheet.write(row, 7, round(cost_usd, 2), center_right)
            worksheet.write(row, 8, company_currency, center_right)
            worksheet.write(row, 9, line.duty_bcd_inr, center_right)
            worksheet.write(row, 10, line.move_id.advance_license_number or '', center)
            worksheet.write(row, 11, round(total_freight, 2), center_right)
            worksheet.write(row, 12, round(total_landed_cost, 2), center_right)
            worksheet.write(row, 13, cost_usd * currency_rate_rec.inverse_company_rate, center_right)
            worksheet.write(row, 14, line.freight or '', center_right)
            worksheet.write(row, 15, line.insurance or '', center_right)
            worksheet.write(row, 16, line.clearingcharge or '', center_right)
            worksheet.write(row, 17, line.liner_charges or '', center_right)
            worksheet.write(row, 18, line.aai_charges or '', center_right)
            worksheet.write(row, 19, line.cfs_charges or '', center_right)
            worksheet.write(row, 20, line.inland_transport or '', center_right)
            worksheet.write(row, 21, line.fine_amt or '', center_right)
            worksheet.write(row, 22, line.int_charges, center_right)
            worksheet.write(row, 23, igst, center_right)
            worksheet.write(row, 24, line.product_id.weight, center_right)
            worksheet.write(row, 25, round(currency_rate_rec.inverse_company_rate, 2), center_right)
            worksheet.write(row, 26, '', center_right)
            if line.product_id.categ_id.display_name == 'Uncovered Flat Sheet':
                attribute_rec = attribute_obj.sudo().search([
                    ('name', '=', 'Thickness')
                ], limit=1)
                if attribute_rec:
                    attribute_line = line.product_id.attribute_line_ids.filtered(
                        lambda line: line.attribute_id.id == attribute_rec.id)
                    if attribute_line and attribute_line[0].value_ids:
                        worksheet.write(row, 26, attribute_line[0].value_ids[0].float_value, center_right)
            elif line.product_id.categ_id.display_name == 'Fabric':
                attribute_rec = attribute_obj.sudo().search([
                    ('name', '=', 'Dimension')
                ], limit=1)
                if attribute_rec:
                    attribute_line = line.product_id.attribute_line_ids.filtered(
                        lambda line: line.attribute_id.id == attribute_rec.id)
                    if attribute_line and attribute_line[0].value_ids:
                        if attribute_line[0].value_ids[0].float_value == 46:
                            worksheet.write(row, 26, round((0.9144 * line.quantity) / 1.12), center_right)
                        else:
                            worksheet.write(row, 26, round((0.9144 * line.quantity) / 1.15), center_right)
            else:
                worksheet.write(row, 26, 1, center_right)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('purchase_register_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "purchase.register.report.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'purchase.register.report.wizard'),
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
