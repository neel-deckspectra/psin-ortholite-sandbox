# -*- coding: utf-8 -*-


from odoo import fields, models

class Company(models.Model):
	_inherit = 'res.company'

	notification_product_type = fields.Selection([
		('template','Product'),
		('variant','Product Variant')
	],default='variant',string='Apply On')
	notification_base = fields.Selection([
		('on_hand','On hand quantity'),
		('fore_cast','Forecast')
	],string='Notification Based On',default='on_hand')
	min_quantity = fields.Float(string='Quantity Limit')
	mix_quantity = fields.Float(string='Maximum Quantity')
	notify_low_stock = fields.Boolean(string="Low Stock Notification?")
	