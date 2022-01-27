# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Shopfloor - Delivery with shipment advice",
    "summary": "Manage delivery process with shipment advices",
    "version": "13.0.1.2.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["sebalix", "TDu"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        # OCA/wms
        "shopfloor",
        # OCA/stock-logistics-transport
        "shipment_advice",
    ],
    "data": ["data/shopfloor_scenario_data.xml", "views/shopfloor_menu.xml"],
    "demo": ["demo/shopfloor_menu_demo.xml"],
}
