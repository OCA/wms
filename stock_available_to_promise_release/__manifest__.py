# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

{
    "name": "Stock Available to Promise Release",
    "version": "14.0.2.3.0",
    "summary": "Release Operations based on available to promise",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Stock Management",
    "depends": [
        "stock",
        # OCA/stock-logistics-workflow
        # This module is not needed per se. But when it is installed it will conflict
        # on the `_action_cancel` of the stock.move model, if executed first.
        # As the module prevent breaking a chain of moves, It is a logical dependency
        # to have.
        "stock_picking_restrict_cancel_with_orig_move",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_product_views.xml",
        "views/stock_move_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_location_route_views.xml",
        "views/res_config_settings.xml",
        "wizards/stock_release_views.xml",
        "wizards/stock_unrelease_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
    "application": False,
    "development_status": "Beta",
}
