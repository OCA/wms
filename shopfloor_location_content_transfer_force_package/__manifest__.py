# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Shopfloor Location Content Transfer Force Select Package",
    "summary": "Force to select package if location already contains packages.",
    "version": "14.0.1.1.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["TDu"],
    "license": "AGPL-3",
    "depends": [
        "shopfloor",
        # OCA/stock-logisticits-warehouse
        "stock_location_package_restriction",
    ],
}
