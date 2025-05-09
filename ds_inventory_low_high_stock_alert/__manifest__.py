# -*- coding: utf-8 -*-

{
    'name': 'Inventory Low & High Stock Alert',
    'version': '17.0.1.0.0',
    'category': 'warehouse',
    'license': 'AGPL-3',
    'description': """ Inventory Low & High Stock Alert """,
    'author': 'DeckSpectra Technologies LLP',
    'website': 'https://www.deckspectra.com/',
    'depends': [
        'base',
        'sale_management',
        'stock',
    ],
    'data': [
        'data/low_stock_notification_cron.xml',
        'views/email_templete.xml',
        'views/stock_config_settings_views.xml',
        'views/inherited_res_users.xml',
    ],
    "application": True,
    "license": "LGPL-3",
}
