# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    "name": "Stock Available to Promise Release",
    "version": "16.0.2.1.0",
    "summary": "Release Operations based on available to promise",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Stock Management",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_product_views.xml",
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_route_views.xml",
        "views/res_config_settings.xml",
        "wizards/stock_release_views.xml",
        "wizards/stock_unrelease_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
    "application": False,
    "development_status": "Beta",
    "pre_init_hook": "pre_init_hook",
}
