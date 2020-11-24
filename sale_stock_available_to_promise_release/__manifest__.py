# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Available to Promise Release - Sale Integration",
    "version": "13.0.1.2.0",
    "summary": "Integration between Sales and Available to Promise Release",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Stock Management",
    "depends": ["sale_stock", "stock_available_to_promise_release", "delivery"],
    "data": [
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "views/product_product_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "license": "AGPL-3",
    "application": False,
    "development_status": "Alpha",
}
