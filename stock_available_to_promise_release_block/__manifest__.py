# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Available to Promise Release - Block",
    "summary": """Block Release of Operations""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp, ACSONE SA/NV, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        # OCA/wms
        "stock_available_to_promise_release",
    ],
    "data": [
        "views/stock_route.xml",
        "views/stock_picking.xml",
        "views/stock_move.xml",
    ],
    "installable": True,
}
