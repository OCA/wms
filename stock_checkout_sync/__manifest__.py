# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Checkout Synchronization",
    "summary": "Sync location for Checkout operations",
    "version": "13.0.1.1.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock_move_common_dest"],
    "data": [
        "views/stock_picking_type_views.xml",
        "views/stock_picking_views.xml",
        "wizards/stock_move_checkout_sync_views.xml",
    ],
}
