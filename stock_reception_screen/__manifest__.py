# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock - Reception screen",
    "summary": "Dedicated screen to receive/scan goods.",
    "version": "14.0.1.0.1",
    "category": "Stock",
    "license": "AGPL-3",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock",
        "product_expiry",
        # OCA/product-attribute
        "product_packaging_dimension",
        "product_packaging_type_pallet",
        # OCA/stock-logistics-workflow
        "stock_quant_package_dimension",
        # OCA/wms
        "stock_storage_type",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/assets.xml",
        "views/stock_move_line.xml",
        "views/stock_picking.xml",
        "views/stock_reception_screen.xml",
        "views/manual_barcode.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
}
