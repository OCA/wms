# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Wms Connector Picking batch",
    "summary": """
        WMS Connector Picking batch""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["wms_connector", "stock_picking_batch"],
    "data": [
        "views/stock_picking_batch.xml",
        "views/stock_warehouse.xml",
    ],
}
