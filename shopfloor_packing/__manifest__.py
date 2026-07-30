# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Packing",
    "version": "16.0.1.0.0",
    "summary": """ Manage Packing into cluster picking""",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Stock Management",
    "depends": [
        "shopfloor",
        "internal_stock_quant_package",
        "delivery_package_type_number_parcels",
        "stock_picking_delivery_package_type_domain",
    ],
    "data": ["views/shopfloor_menu.xml", "views/stock_picking.xml"],
    "installable": True,
    "license": "AGPL-3",
    "application": False,
}
