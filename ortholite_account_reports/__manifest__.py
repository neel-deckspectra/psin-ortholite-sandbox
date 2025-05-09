# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Invoice Report Changes',
    'version': '17.0.1.0.0',
    'description': "Whenever any customer comes under SEZ (Special Economic Zone) in GST Treatment then e-invoice comes with custom header otherwise standard invoice will be printed.",
    'depends': [
        'contacts',
        'account_accountant',
        'l10n_in_edi',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/report_external_layout_template.xml",
        "views/report_invoice.xml",
        "wizard/purchase_register_report_wizard_views.xml",
        "views/account_move_views.xml",
        "wizard/sale_register_report_wizard_views.xml",
        "wizard/to_invoice_bill_orders_wizard_views.xml",
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}