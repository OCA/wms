# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Geoengine",
    "summary": """Release channel based on geo-localization""",
    "version": "16.0.2.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["geoengine_partner", "stock_release_channel"],
    "data": [
        "views/res_partner.xml",
        "views/stock_release_channel.xml",
    ],
    "demo": [],
}
