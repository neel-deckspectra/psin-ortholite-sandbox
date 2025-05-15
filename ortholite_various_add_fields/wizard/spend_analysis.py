from odoo import models, fields, api
from odoo.exceptions import UserError

class SpendAnalysisWizard(models.TransientModel):
    _name = 'spend.analysis.wizard'
    _description = 'Spend Analysis Wizard'

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    vendor = fields.Many2one('res.partner', string='Vendor')
    vendor_category_id = fields.Many2one('res.partner.category', string='Vendor Category',)
    product_categ_id = fields.Many2one('product.category', string='Product Category')

    @api.constrains('start_date', 'end_date')
    def action_generate_report(self):
        if self.start_date > self.end_date:
            raise UserError("End date must be greater than the start date.")

    def print_xls_report(self):
        import xlwt
        import io
        import base64
        from odoo.exceptions import UserError

        workbook = xlwt.Workbook(encoding='utf-8')
        heading_format = xlwt.easyxf(
            'font:height 300,bold True; align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold = xlwt.easyxf(
            'font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        bold_center = xlwt.easyxf(
            'font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        worksheet = workbook.add_sheet('Spend Analysis', bold_center)
        bold_center_total = xlwt.easyxf(
            'font:height 220,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center = xlwt.easyxf('align: horiz left; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        center_right = xlwt.easyxf('align: horiz right; borders: top_color black, bottom_color black, right_color black, left_color black, left thin, right thin, top thin, bottom thin;')
        start_date = self.start_date.strftime('%m-%d-%Y')
        end_date = self.end_date.strftime('%m-%d-%Y')
        worksheet.write_merge(0, 1, 0, 16, self.env.user.company_id.name, heading_format)
        worksheet.write_merge(2, 2, 0, 16, '')
        worksheet.write_merge(3, 4, 0, 16, 'Spend Analysis', heading_format)
        worksheet.write_merge(5, 5, 0, 16, '')
        worksheet.write_merge(6, 7, 0, 16, ('Start Date: %s End Date: %s' % (start_date, end_date)), heading_format)
        worksheet.write_merge(8, 8, 0, 16, '')

        # Query stock.picking records filtered by start_date and end_date if provided
        stock_picking_obj = self.env['stock.picking']
        domain = []
        if self.start_date:
            domain.append(('date_done', '>=', self.start_date))
        if self.end_date:
            domain.append(('date_done', '<=', self.end_date))
        records = stock_picking_obj.search(domain)

        # Write headers
        headers = [
            "Effective Date", "Vendor Code", "Vendor Category", "Vendor", "Vendor reference",
            "Category", "Item Code", "Product Name", "Unit Of Measure", "Brand", "Size",
            "Order quantity", "Unit Prices", "value", "Currency Con value", "Currency", "Total Thickness"
        ]
        for col, header in enumerate(headers):
            worksheet.write(9, col, header, bold_center_total)

        # Write data rows
        for row, record in enumerate(records, start=10):
            # Effective Date
            worksheet.write(row, 0, record.date_done.strftime('%Y-%m-%d') if record.date_done else '', center)
            # Vendor Code (partner_id.ref)
            worksheet.write(row, 1, record.partner_id.ref if record.partner_id else '', center)
            # Vendor Category (partner_id.category_id name)
            vendor_categs = record.partner_id.category_id.mapped('name') if record.partner_id else []
            worksheet.write(row, 2, ', '.join(vendor_categs), center)
            # Vendor (partner_id name)
            worksheet.write(row, 3, record.partner_id.name if record.partner_id else '', center)
            # Vendor reference (partner_id.ref)
            worksheet.write(row, 4, record.partner_id.ref if record.partner_id else '', center)
            # Category (picking_type_id.name)
            worksheet.write(row, 5, record.picking_type_id.name if record.picking_type_id else '', center)
            # Item Code (product_ids product_tmpl_id default_code) - aggregate unique codes from move_line_ids
            item_codes = record.move_line_ids.mapped('product_id.default_code')
            worksheet.write(row, 6, ', '.join(filter(None, item_codes)), center)
            # Product Name (product_ids product_tmpl_id name) - aggregate unique names from move_line_ids
            product_names = record.move_line_ids.mapped('product_id.name')
            worksheet.write(row, 7, ', '.join(filter(None, product_names)), center)
            # Unit Of Measure (product_uom_id name) - aggregate unique uoms from move_line_ids
            uoms = record.move_line_ids.mapped('product_uom_id.name')
            worksheet.write(row, 8, ', '.join(filter(None, uoms)), center)
            # Brand (product brand_id name) - field not present, write empty string
            brands = ['']  # No brand field available
            worksheet.write(row, 9, '', center)
            # Size (product size or attribute) - aggregate unique sizes from move_line_ids (assuming attribute 'size')
            sizes = []
            for line in record.move_line_ids:
                size = False
                if line.product_id.product_tmpl_id.attribute_line_ids:
                    for attr_line in line.product_id.product_tmpl_id.attribute_line_ids:
                        if attr_line.attribute_id.name.lower() == 'size':
                            size_vals = attr_line.value_ids.mapped('name')
                            sizes.extend(size_vals)
                # fallback to product size field if exists
                if hasattr(line.product_id, 'size'):
                    sizes.append(line.product_id.size)
            sizes = list(set(filter(None, sizes)))
            worksheet.write(row, 10, ', '.join(sizes), center)
            # Order quantity (move_line_ids qty_done sum)
            qty = sum(record.move_line_ids.mapped('qty_done'))
            worksheet.write(row, 11, qty, center_right)
            # Unit Prices (move_line_ids move_id.price_unit average)
            prices = [line.move_id.price_unit for line in record.move_line_ids if line.move_id and line.move_id.price_unit]
            avg_price = sum(prices) / len(prices) if prices else 0
            worksheet.write(row, 12, avg_price, center_right)
            # value (sum of move_id.price_unit * qty_done)
            value = sum(line.move_id.price_unit * line.qty_done for line in record.move_line_ids if line.move_id and line.move_id.price_unit and line.qty_done)
            worksheet.write(row, 13, value, center_right)
            # Currency Con value (assuming currency rate applied, use value for now)
            worksheet.write(row, 14, value, center_right)
            # Currency (from partner pricelist currency)
            currency_name = ''
            if record.partner_id and record.partner_id.property_product_pricelist:
                currency = record.partner_id.property_product_pricelist.currency_id
                if currency:
                    currency_name = currency.name
            worksheet.write(row, 15, currency_name, center)
            # Total Thickness (custom field or sum of thickness from move_line_ids, assuming thickness field on product)
            thicknesses = []
            for line in record.move_line_ids:
                thickness = getattr(line.product_id, 'thickness', False)
                if thickness:
                    thicknesses.append(thickness)
            total_thickness = sum(thicknesses) if thicknesses else 0
            worksheet.write(row, 16, total_thickness, center_right)

        fp = io.BytesIO()
        workbook.save(fp)
        data = base64.encodebytes(fp.getvalue())
        IrAttachment = self.env['ir.attachment']
        report_name = str('spend_analysis_report_' + start_date + '_' + end_date + '.xls')
        attachment_vals = {
            "name": report_name,
            "res_model": "spend.analysis.wizard",
            "type": "binary",
            "datas": data,
            "public": True,
        }
        fp.close()
        attachment = IrAttachment.sudo().search([
            ('res_model', '=', 'spend.analysis.wizard'),
            ('type', '=', 'binary')
        ])
        if attachment:
            attachment.unlink()
        attachment = IrAttachment.create(attachment_vals)
        if not attachment:
            raise UserError(_('There is no attachments...'))
        url = "/web/content/" + str(attachment.id) + "?download=true"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

        
