# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Shopfloor Location Package Restriction",
    "summary": "Glue module between shopfloor and location package restriction",
    "version": "14.0.1.0.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "shopfloor",
        # OCA/stock-logistics-warehouse
        "stock_location_package_restriction",
    ],
    "auto_install": True,
}
