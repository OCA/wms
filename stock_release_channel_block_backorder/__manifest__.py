# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel - Block Backorder",
    "summary": """Block delivery of unavailable backorders.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, BCIM, Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        # OCA/wms
        "stock_release_channel",
    ],
    "data": ["views/stock_picking.xml"],
    "installable": True,
}
