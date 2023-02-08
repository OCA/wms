# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Internal Stock Quant Package",
    "summary": "This module allows to declare internal stock quant package",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-tracking",
    "depends": ["stock", "delivery_procurement_group_carrier"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_quant_package_views.xml",
        "views/stock_picking_type_views.xml",
    ],
    "installable": True,
}
