# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor - Batch Transfer Automatic Creation",
    "summary": "Create batch transfers for Cluster Picking",
    "version": "16.0.1.1.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["guewen"],
    "license": "AGPL-3",
    "application": False,
    "depends": ["shopfloor", "stock_picking_batch_creation"],
    "data": [
        "views/shopfloor_menu_views.xml",
        "views/stock_device_type.xml",
    ],
    "installable": True,
}
