# -*- coding: utf-8 -*-
# Copyright 2020 Dishon Kadoh <https://realestdon.github.io/>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Frontdesk Extend',
    'version': '17.0.1.0.0',
    'category': 'Localization',
    'license': 'AGPL-3',
    'description': """ 
    Fontdesk Extension
   """,
    'author': 'DeckSpectra Technologies LLP',
    'website': 'https://www.deckspectra.com/',
    'depends': ["frontdesk"],
    'data': [
        'views/frontdesk_visitor_view.xml'
    ],

    'assets': {
        'frontdesk.assets_frontdesk': [
            "ds_ortholite_frontdesk/static/src/js/visitor_form_extend.js",
            "ds_ortholite_frontdesk/static/src/xml/visitor_form.xml",
            "ds_ortholite_frontdesk/static/src/xml/register_page.xml",
        ]
    },
    "application": True,
    "license": "LGPL-3",
}
