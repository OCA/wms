# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Release Channel Split",
    "summary": """This module is a glue module between shopfloor and
    stock_release_channel module in order to keep release channel on a picking in
    the split flow""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "maintainers": ["rousseldenis"],
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "shopfloor",
        "stock_release_channel",
    ],
    "auto_install": True,
}
