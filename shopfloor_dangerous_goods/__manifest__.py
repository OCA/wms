# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Shopfloor Dangerous Goods",
    "summary": "Glue Module Between Shopfloor and Stock Dangerous Goods",
    "version": "14.0.1.1.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        "shopfloor",
        # OCA/stock-logistics-workflow
        "stock_dangerous_goods",
    ],
    "data": [],
}
