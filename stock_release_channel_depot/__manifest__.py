# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Release Channel Depot",
    "summary": """This module allows users to add partner depot to stock release channel.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["stock_depot", "stock_release_channel"],
    "data": [
        "views/stock_release_channel_views.xml",
        "views/stock_picking.xml",
    ],
}
