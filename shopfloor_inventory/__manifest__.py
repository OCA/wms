# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor Inventory",
    "summary": "manage stock inventories with barcode scanners",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["guewen", "simahawk", "sebalix"],
    "license": "AGPL-3",
    "application": False,
    "depends": [
        "shopfloor",
        "stock_inventory_user",
        "stock_inventory_location_state",
    ],
    "data": [
        "data/shopfloor_scenario_data.xml",
        "views/shopfloor_menu.xml",
        "views/stock_inventory.xml",
    ],
    "demo": [
        "demo/shopfloor_menu_demo.xml",
    ],
    "installable": True,
}
