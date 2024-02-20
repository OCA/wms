# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Delivery",
    "summary": """
        Add a carrier selection criteria on the release channel """,
    "version": "16.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,BCIM,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel",
        "delivery",
    ],
    "data": ["views/stock_release_channel_views.xml"],
    "demo": [],
}
