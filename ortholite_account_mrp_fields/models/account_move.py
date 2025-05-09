# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import xlwt
import io


class AccountMove(models.Model):
    _inherit = "account.move"

    brand_ids = fields.Many2many("crm.tag", string="Brand", readonly=True)

    def action_post(self):
        # Set validation on invoice quantity base on sale order quantity
        for invoice in self:
            if invoice.move_type == 'out_invoice':
                for line in invoice.invoice_line_ids:
                    sale_order_ids = line.mapped('sale_line_ids.order_id')
                    for sale_order_id in sale_order_ids:
                        sale_order_line_rec = self.env['sale.order.line'].search([
                            ('product_id', '=', line.product_id.id),
                            ('order_id', '=', sale_order_id.id),
                            ('order_id.state', 'in', ['sale', 'done']),
                            ('order_id.partner_invoice_id', '=', self.partner_id.id)
                        ])
                        if sale_order_line_rec:
                            account_move_line_posted_rec = self.env['account.move.line'].search([
                                ('product_id', '=', line.product_id.id),
                                ('move_id.state', '=', 'posted'),
                                ('move_id.payment_state', '!=', 'reversed'),
                                ('move_id.partner_id', '=', self.partner_id.id),
                                ('sale_line_ids', 'in', sale_order_line_rec.ids)
                            ])
                            account_move_line_reversed_rec = self.env['account.move.line'].search([
                                ('product_id', '=', line.product_id.id),
                                ('move_id.state', '=', 'posted'),
                                ('move_id.payment_state', '=', 'reversed'),
                                ('move_id.partner_id', '=', self.partner_id.id),
                                ('sale_line_ids', 'in', sale_order_line_rec.ids)
                            ])
                            so_quantity = sum(sale_order_line_rec.mapped('product_uom_qty'))
                            posted_invoice_quantity = sum(account_move_line_posted_rec.mapped('quantity'))
                            reversed_invoice_quantity = sum(account_move_line_reversed_rec.mapped('quantity'))
                            invoice_quantity = posted_invoice_quantity - reversed_invoice_quantity
                            if (line.quantity + invoice_quantity) > so_quantity:
                                raise ValidationError(_('Invoiced quantity exceeds the order, Please correct!'))
        return super(AccountMove, self).action_post()

    def action_unpaid_bill_reminder(self):
        # send unpaid bill reminder email account team
        mail_template = self.env.ref('ortholite_account_mrp_fields.email_template_vendor_payment_due_alerts')
        billing_group_id = self.env.ref('account.group_account_invoice').id
        invoice_rec = self.search([
            ("state", "=", "posted"),
            ("payment_state", "!=", "paid"),
            ("move_type", "=", "in_invoice"),
            ("invoice_date_due", "<=", fields.Date.today()),
        ])
        users_rec = self.env['res.users'].sudo().search([
            ('groups_id', 'in', billing_group_id)
        ])
        # generate excel file
        date = fields.Date.today().strftime('%d-%m-%Y')
        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet("Vendor'a Payment Due Alerts", bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet.write_merge(
            0, 1, 0, 4, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 4, '')
        worksheet.write_merge(
            3, 4, 0, 4, "Vendor'a Payment Due Alerts", heading_format)
        worksheet.write_merge(5, 5, 0, 4, '')
        worksheet.write_merge(6, 7, 0, 4, str(date), heading_format)
        worksheet.write_merge(8, 8, 0, 4, '')
        worksheet.col(0).width = int(25 * 260)
        worksheet.col(1).width = int(70 * 260)
        worksheet.col(2).width = int(15 * 260)
        worksheet.col(3).width = int(15 * 260)
        worksheet.col(4).width = int(15 * 260)
        worksheet.write(9, 0, "Invoice Number", bold_center_total)
        worksheet.write(9, 1, "Vendor", bold_center_total)
        worksheet.write(9, 2, "Bill Date", bold_center_total)
        worksheet.write(9, 3, "Due Date", bold_center_total)
        worksheet.write(9, 4, "Amount Due", bold_center_total)
        row = 10
        for invoice in invoice_rec:
            worksheet.write(row, 0, invoice.name or '', center)
            worksheet.write(row, 1, invoice.partner_id.name or '', center)
            worksheet.write(row, 2, invoice.invoice_date.strftime('%d-%m-%Y') or '', center)
            worksheet.write(row, 3, invoice.invoice_date_due.strftime('%d-%m-%Y') or '', center)
            worksheet.write(row, 4, invoice.amount_residual or 0.0, center_right)
            row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('vendor_payment_due_alerts_' + date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "account.move",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'account.move'),
            ('type', '=', 'binary'),
            ('public', '=', True),
        ])
        if attachment:
            attachment.unlink()
        attachment = IrAttachment.create(attachment_vals)
        email_values = {
            'recipient_ids': [(4, user.partner_id.id) for user in users_rec],
            'attachment_ids': [(4, attachment.id)],
        }
        if mail_template and attachment:
            # send mail.
            mail_template.send_mail(self.id, force_send=True, email_values=email_values)