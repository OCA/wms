# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Available to Promise Release - Block from Sales",
    "summary": """Block release of deliveries from sales orders.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptcamp, ACSONE SA/NV, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        # OCA/wms
        "sale_stock_available_to_promise_release",
        "stock_available_to_promise_release_block",
    ],
    "data": [
        "views/sale_order.xml",
        "views/sale_order_line.xml",
    ],
    "installable": True,
}
