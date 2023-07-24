# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock Warehouse Flow Product Packaging",
    "summary": "Configure packaging types on routing flows for stock moves",
    "author": "MT Software, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "14.0.2.0.0",
    "license": "AGPL-3",
    "depends": [
        "stock_warehouse_flow",
        # OCA/product-attribute
        "product_packaging_type",
    ],
    "demo": [],
    "data": [
        "views/stock_warehouse_flow.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["mt-software-de"],
}
