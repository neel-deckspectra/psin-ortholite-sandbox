# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'Customer Approvals',
    'version': '17.0.1.0',
    'license': "OPL-1",
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'category': 'Human Resources/Approvals',
    'depends': [
        'approvals',
        'contacts'
    ],
    "summary": 'This module create the approval request for creating a Customer. | Customer Approval | Approval Request | Customer Request | Approval | Customer | Request | Customer Approve | Approve Request | Partner Approval | Vendor Approval',
    'description': """
This module used to generate creation approval request for new customer creation.
    """,
    'data': [
        "security/security.xml",
        "data/approval_category_data.xml",
        "views/approval_category_views.xml",
        "views/approval_request_views.xml",
        "views/res_partner_views.xml",
    ],
    'images': [
        'static/description/banner.gif'
    ],
    'installable': True,
    'price': 29,
    'currency': 'EUR'
}
