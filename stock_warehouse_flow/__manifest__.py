# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock Warehouse Flow",
    "summary": "Configure routing flow for stock moves",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "14.0.1.0.3",
    "license": "AGPL-3",
    "depends": [
        # core
        "stock",
        "delivery",
        # OCA/stock-logistics-workflow
        "delivery_procurement_group_carrier",
    ],
    "demo": [
        "demo/stock_warehouse_flow.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_location_route.xml",
        "views/stock_warehouse_flow.xml",
        "views/stock_warehouse.xml",
        "views/delivery_carrier.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
}
