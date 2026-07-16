# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Search Filter",
    "summary": """Choose which barcodes (products, lots, locations, ...)
    can be scanned in each Shopfloor menu.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["shopfloor"],
    "data": [
        "views/shopfloor_menu.xml",
    ],
    "demo": [],
}
