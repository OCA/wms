# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Location Storage Type Strategy",
    "summary": "Apply storage type strategy on move destination location",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_storage_type",
        "stock_quant_package_product_packaging",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_location.xml",
        "views/stock_quant_package.xml",
        "views/stock_package_storage_location.xml",
        "views/stock_package_storage_type.xml",
    ],
    "demo": [
        "demo/stock_location.xml",
        "demo/stock_location_storage_type.xml",
        "demo/stock_package_storage_location.xml",
    ],
}
