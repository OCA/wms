# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020 BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor - Manual Product Transfer",
    "summary": "Manage manual product transfers",
    "version": "14.0.1.5.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        # OCA/wms
        "shopfloor",
        # OCA/stock-logistics-workflow
        "stock_restrict_lot",
    ],
    "data": [
        "data/shopfloor_scenario.xml",
    ],
    "demo": ["demo/stock_picking_type.xml", "demo/shopfloor_menu.xml"],
    "installable": True,
}
