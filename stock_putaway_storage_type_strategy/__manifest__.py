# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Putaway Storage Type Strategy",
    "summary": "Advanced putaway storage selection for WMS",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_putaway_rule",
        "stock_storage_type",
    ],
    "data": [
        "views/stock_location.xml",
        "views/stock_location_storage_type.xml",
    ],
    "demo": [
        "demo/stock_putaway_rule.xml",
        "demo/location_storage_type.xml",
    ]
}
