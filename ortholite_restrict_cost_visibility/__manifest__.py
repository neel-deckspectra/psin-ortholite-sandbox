# -*- coding: utf-8 -*-
{
    'name': "Cost Visibility",
    'description': "Restirct the user to displaying the cost in various apps",
    'odoo_task_id': "3822790",
    'author': "Odoo PS-IN",
    'website': "https://www.odoo.com/",
    'category': 'Customization',
    'version': '1.0',
    'depends': [
        'account_accountant',
        'stock_account',
        'mrp',
        'mrp_workorder',
    ],
    'data': [
        'security/ortholite_security.xml',
        'views/account_views.xml',
        'views/mrp_views.xml',
        'views/product_views.xml',
        'views/stock_views.xml',
        'report/mrp_report_views_main.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ortholite_restrict_cost_visibility/static/src/**/*',
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
    'license' : 'LGPL-3',
}
