# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Cluster Picking Repack Mobile",
    "version": "18.0.1.0.0",
    "summary": """
    Shopfloor mobile extension for packing operation into cluster picking
    """,
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-shopfloor",
    "category": "Stock Management",
    "depends": ["shopfloor_mobile", "shopfloor_cluster_picking_repack"],
    "data": ["templates/assets.xml"],
    "installable": True,
    "license": "AGPL-3",
    "application": False,
}
