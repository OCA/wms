# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Location Storage Type Strategy",
    "summary": "Apply storage type strategy on move destination location",
    "version": "13.0.1.0.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_location_children",
        "stock_quant_package_dimension",
        "stock_storage_type",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_location.xml",
        "views/stock_quant_package.xml",
        "views/stock_package_level.xml",
        "views/stock_package_storage_type.xml",
        "views/stock_storage_location_sequence.xml",
    ],
    "demo": [
        "demo/product_packaging.xml",
        "demo/stock_location.xml",
        "demo/stock_location_storage_type.xml",
        "demo/stock_storage_location_sequence.xml",
    ],
}
