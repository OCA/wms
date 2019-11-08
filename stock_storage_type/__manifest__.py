# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Storage Type",
    "summary": "Manage packages and locations storage types",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_packaging.xml",
        "views/stock_location.xml",
        "views/stock_location_storage_type.xml",
        "views/stock_package_storage_type.xml",
        "views/stock_picking.xml",
        "views/storage_type_menus.xml",
    ],
    "demo": [
        "demo/stock_location_storage_type.xml",
        "demo/stock_package_storage_type.xml",
        "demo/product_packaging.xml",
        "demo/stock_location.xml",
    ],
}
