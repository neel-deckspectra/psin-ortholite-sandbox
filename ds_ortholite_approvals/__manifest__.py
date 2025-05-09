# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Product and BOM Approvals',
    'version': '17.0.1.0.0',
    'category': 'Localization',
    'license': 'AGPL-3',
    'description': """ 
    Product and BOM Approvals
   """,
    'author': 'DeckSpectra Technologies LLP',
    'website': 'https://www.deckspectra.com/',
    'depends': [
        "mrp",
        "customer_approvals",
        "sale_management",
        "purchase",
        "account",
        "stock_landed_costs",
        "quality_control",
        "ortholite_various_add_fields",
        "ortholite_sales",
        "ortholite_restrict_cost_visibility",
        "mrp_plm"
    ],
    'data': [
        'data/approval_data.xml',
        'views/approval_category_request_views.xml',
    ],
    "application": True,
    "license": "LGPL-3",
}
