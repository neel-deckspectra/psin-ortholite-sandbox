# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Ortholite CRM-PLM",
    'summary': 'Ortholite crm and plm connection',
    "version": "1.0",
    'website': 'https://www.odoo.com',
    'author': 'Odoo PSIN',
    'description': """
        - TASK ID - 3713914
        - added magic button in lead to directly go PLM
        - added product category and product attribute value in lead
        - added crm opportunity and contact in PLM
    """,
    'category': 'Customization',
    'depends': ['crm','mrp_plm', 'ortholite_account_mrp_fields'],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
        'views/mrp_eco_view.xml',
        'wizard/sample_tracking_report_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'odoo_task_id': '3713914',
}
