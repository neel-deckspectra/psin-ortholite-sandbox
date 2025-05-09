# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from ast import literal_eval
from odoo import SUPERUSER_ID
import base64
import xlwt
import io


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notification_product_type = fields.Selection([
        ('template', 'Product'),
        ('variant', 'Product Variant')
    ],related='company_id.notification_product_type', string='Apply On', readonly=False)
    notification_base = fields.Selection([
        ('on_hand', 'On hand quantity'),
        ('fore_cast', 'Forecast')
    ],related='company_id.notification_base', string='Notification Based On', readonly=False)
    min_quantity = fields.Float(string='Quantity Limit', related='company_id.min_quantity', readonly=False)
    mix_quantity = fields.Float(string='Maximum Quantity', related='company_id.mix_quantity', readonly=False)

    def get_low_stock_product_list(self):
        resConfig_rec = self.env['res.config.settings'].new()
        products_list = []
        if resConfig_rec.notification_base == 'on_hand':
            if resConfig_rec.notification_product_type == 'variant':
                result = self.env['product.product'].search([
                    ('qty_available', '<', resConfig_rec.min_quantity),
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    total_quant = 0.0
                    stock_quant = self.env['stock.quant'].search([
                        ('product_id', '=', product.id),
                        ('on_hand', '=', True),
                        ('company_id', 'in', self.env.companies.ids)
                    ])
                    for quant in stock_quant:
                        total_quant += quant.quantity
                    if total_quant < resConfig_rec.min_quantity:
                        products_list.append([{
                            'name': product.display_name,
                            'limit_quantity': resConfig_rec.min_quantity,
                            'stock_quantity': total_quant
                        }])
            else:
                result = self.env['product.template'].search([
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    total_quant = 0.0
                    stock_quant = self.env['stock.quant'].search([
                        ('product_tmpl_id', '=', product.id),
                        ('on_hand', '=', True),
                        ('company_id', 'in', self.env.companies.ids)
                    ])
                    for quant in stock_quant:
                        total_quant += quant.quantity
                    if total_quant < resConfig_rec.min_quantity:
                        products_list.append([{
                            'name': product.display_name,
                            'limit_quantity': resConfig_rec.min_quantity,
                            'stock_quantity': total_quant
                        }])
        if resConfig_rec.notification_base == 'fore_cast':
            if resConfig_rec.notification_product_type == 'variant':
                result = self.env['product.product'].search([
                    ('virtual_available', '<', resConfig_rec.min_quantity),
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    products_list.append([{
                        'name': product.display_name,
                        'limit_quantity': resConfig_rec.min_quantity,
                        'stock_quantity': product.virtual_available
                    }])
            else:
                result = self.env['product.template'].search([
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    if product.virtual_available < resConfig_rec.min_quantity:
                        products_list.append([{
                            'name': product.display_name,
                            'limit_quantity': resConfig_rec.min_quantity,
                            'stock_quantity': product.virtual_available
                        }])
        return products_list

    def get_high_stock_product_list(self):
        resConfig_rec = self.env['res.config.settings'].new()
        products_list = []
        if resConfig_rec.notification_base == 'on_hand':
            if resConfig_rec.notification_product_type == 'variant':
                result = self.env['product.product'].search([
                    ('qty_available', '>', resConfig_rec.mix_quantity),
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    total_quant = 0.0
                    stock_quant = self.env['stock.quant'].search([
                        ('product_id', '=', product.id),
                        ('on_hand', '=', True),
                        ('company_id', 'in', self.env.companies.ids)
                    ])
                    for quant in stock_quant:
                        total_quant += quant.quantity
                    if total_quant > resConfig_rec.mix_quantity:
                        products_list.append([{
                            'name': product.display_name,
                            'limit_quantity': resConfig_rec.mix_quantity,
                            'stock_quantity': total_quant
                        }])
            else:
                result = self.env['product.template'].search([
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    total_quant = 0.0
                    stock_quant = self.env['stock.quant'].search([
                        ('product_tmpl_id', '=', product.id),
                        ('on_hand', '=', True),
                        ('company_id', 'in', self.env.companies.ids)
                    ])
                    for quant in stock_quant:
                        total_quant += quant.quantity
                    if total_quant > resConfig_rec.mix_quantity:
                        products_list.append([{
                            'name': product.display_name,
                            'limit_quantity': resConfig_rec.mix_quantity,
                            'stock_quantity': total_quant
                        }])
        if resConfig_rec.notification_base == 'fore_cast':
            if resConfig_rec.notification_product_type == 'variant':
                result = self.env['product.product'].search([
                    ('virtual_available', '>', resConfig_rec.mix_quantity),
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    products_list.append([{
                        'name': product.display_name,
                        'limit_quantity': resConfig_rec.mix_quantity,
                        'stock_quantity': product.virtual_available
                    }])
            else:
                result = self.env['product.template'].search([
                    ('detailed_type', '=', 'product'),
                    ('is_fg_product', '=', False),
                    '|',
                    ('is_materials', '=', True),
                    ('is_general_item', '=', True),
                ])
                for product in result:
                    if product.virtual_available > resConfig_rec.mix_quantity:
                        products_list.append([{
                            'name': product.display_name,
                            'limit_quantity': resConfig_rec.mix_quantity,
                            'stock_quantity': product.virtual_available
                        }])
        return products_list

    def generate_excel_file(self, company):
        date = fields.Date.today().strftime('%d-%m-%Y')
        low_stock_product_list = self.get_low_stock_product_list()
        high_stock_product_list = self.get_high_stock_product_list()
        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet('Low Stock', bold_center)
        worksheet_high_stock = workbook.add_sheet('High Stock', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet.write_merge(
            0, 1, 0, 2, company.name, heading_format)
        worksheet_high_stock.write_merge(
            0, 1, 0, 2, company.name, heading_format)
        worksheet.write_merge(2, 2, 0, 2, '')
        worksheet_high_stock.write_merge(2, 2, 0, 2, '')
        worksheet.write_merge(
            3, 4, 0, 2, 'Inventory Low Stock Alert', heading_format)
        worksheet_high_stock.write_merge(
            3, 4, 0, 2, 'Inventory High Stock Alert', heading_format)
        worksheet.write_merge(5, 5, 0, 2, '')
        worksheet_high_stock.write_merge(5, 5, 0, 2, '')
        worksheet.write_merge(6, 7, 0, 2, str(date), heading_format)
        worksheet_high_stock.write_merge(6, 7, 0, 2, str(date), heading_format)
        worksheet.write_merge(8, 8, 0, 2, '')
        worksheet_high_stock.write_merge(8, 8, 0, 2, '')
        worksheet.col(0).width = int(140 * 260)
        worksheet_high_stock.col(0).width = int(140 * 260)
        worksheet.col(1).width = int(25 * 260)
        worksheet_high_stock.col(1).width = int(25 * 260)
        worksheet.col(2).width = int(25 * 260)
        worksheet_high_stock.col(2).width = int(25 * 260)
        worksheet.write(9, 0, "Product Name", bold_center_total)
        worksheet_high_stock.write(9, 0, "Product Name", bold_center_total)
        worksheet.write(9, 1, "Available Quantity", bold_center_total)
        worksheet_high_stock.write(9, 1, "Available Quantity", bold_center_total)
        worksheet.write(9, 2, "Required Quantity", bold_center_total)
        worksheet_high_stock.write(9, 2, "Required Quantity", bold_center_total)
        low_stock_row = 10
        high_stock_row = 10
        for product in low_stock_product_list:
            worksheet.write(low_stock_row, 0, product[0].get('name') or '', center)
            worksheet.write(low_stock_row, 1, product[0].get('stock_quantity') or 0, center_right)
            worksheet.write(low_stock_row, 2, product[0].get('limit_quantity') or 0, center_right)
            low_stock_row += 1
        for product in high_stock_product_list:
            worksheet_high_stock.write(high_stock_row, 0, product[0].get('name') or '', center)
            worksheet_high_stock.write(high_stock_row, 1, product[0].get('stock_quantity') or 0, center_right)
            worksheet_high_stock.write(high_stock_row, 2, product[0].get('limit_quantity') or 0, center_right)
            high_stock_row += 1
        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('inventory_low_high_stock_alert_' + date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "res.config.settings",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'res.config.settings'),
            ('type', '=', 'binary')
        ])
        if attachment:
            attachment.unlink()
        attachment = IrAttachment.create(attachment_vals)
        return attachment.id

    def action_low_stock_send(self):
        company_rec = self.env['res.company'].search([('notify_low_stock', '=', True)])
        mail_template = self.env.ref('ds_inventory_low_high_stock_alert.low_stock_email_template')
        users_rec = self.env['res.users'].sudo().search([
            ('notify_user', '=', True)
        ])
        for company in company_rec:
            if mail_template:
                attachment = self.generate_excel_file(company)
                if attachment:
                    email_values = {
                        'recipient_ids': [(4, user.partner_id.id) for user in users_rec],
                        'attachment_ids': [(4, attachment)],
                    }
                    mail_template.send_mail(self, force_send=True, email_values=email_values)
        return True
