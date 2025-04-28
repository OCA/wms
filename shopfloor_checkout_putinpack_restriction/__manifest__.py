# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Shopfloor Checkout Put In Pack Restriction",
    "summary": "",
    "version": "14.0.1.2.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Raumschmiede, Odoo Community Association (OCA)",
    "maintainers": ["TDu"],
    "license": "AGPL-3",
    "depends": [
        # OCA/wms
        "shopfloor",
        # OCA/stock-logistics-workflow
        "stock_picking_putinpack_restriction",
    ],
    "installable": True,
}
