# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Split Picking With Release Channel Propagate Picking",
    "summary": """Glue module to preserve the release channel on picking split""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel_propagate_channel_picking",
        "stock_split_picking",
    ],
    "data": [],
    "demo": [],
    "installable": True,
    "auto_install": True,
}
