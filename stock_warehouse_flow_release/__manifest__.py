# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock Warehouse Flow (release integration)",
    "summary": "Warehouse flows integrated with Operation Release",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "depends": [
        # OCA/wms
        "stock_warehouse_flow",
        "stock_available_to_promise_release",
    ],
    "data": [],
    "installable": True,
    "development_status": "Alpha",
}
