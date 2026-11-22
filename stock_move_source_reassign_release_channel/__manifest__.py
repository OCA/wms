# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Move Source Reassign Release Channel",
    "summary": """This module allows to choose the release channel where to
    reassign the moves""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "maintainers": ["rousseldenis"],
    "depends": ["stock_move_source_reassign", "stock_release_channel"],
    "data": ["wizards/stock_move_reassign.xml"],
}
