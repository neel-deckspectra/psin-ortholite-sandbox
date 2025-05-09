# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Sales Customization",
    'version': '1.0',
    'summary': 'Sales',
    'license': 'LGPL-3',
    'description': """
        Sales Customization - Task ID: 3946632,
        Add a field in the Sales Analysis model for filter and groupby records with tags
    """,

    # auther
    'author': "Odoo PS-IN",
    'website': "http://www.odoo.com",
    'category': "Customizations",

    # any module necessary for this one to work correctly
    'depends': ['sale_management', 'crm_iap_mine', 'website_crm_iap_reveal', 'crm_lead_product', 'ortholite_account_mrp_fields', 'sale_purchase_inter_company_rules', 'contacts', 'phone_validation'],

    #Data
    'data': [
        'data/partner_code_sequence.xml',
        'security/ir.model.access.csv',
        'report/sale_report_views.xml',
        'views/sales_order_views.xml',
        'views/res_users_views.xml',
        'views/crm_menu_views.xml',
        'views/crm_lead_views.xml',
        'wizard/crm_lead_line_wizard_views.xml',
        'wizard/sales_forecast_excel_report_wizard_views.xml',
        'views/season_views.xml',
        'views/res_partner_views.xml',
        'views/mail_activity_type_views.xml',
        'wizard/mail_activity_schedule_views.xml',
        'wizard/activity_tracking_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ortholite_sales//static/src/**/*',
        ]
    },

    'installable': True,
    'application': False,
}
