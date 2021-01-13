# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Stock Available to Promise Release - Sale Integration",
    "version": "13.0.1.4.1",
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
    "license": "LGPL-3",
    "application": False,
    "development_status": "Alpha",
}
