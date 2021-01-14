# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    "name": "Stock Available to Promise Release",
    "version": "13.0.1.9.2",
    "summary": "Release Operations based on available to promise",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Stock Management",
    "website": "https://github.com/OCA/wms",
    "depends": ["stock"],
    "data": [
        "views/product_product_views.xml",
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_location_route_views.xml",
        "views/res_config_settings.xml",
        "wizards/stock_release_views.xml",
    ],
    "installable": False,
    "license": "LGPL-3",
    "application": False,
    "development_status": "Alpha",
}
