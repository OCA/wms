# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Wms Connector",
    "summary": """
        WMS Connector""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["stock", "sale", "attachment_synchronize"],
    "data": [
        "security/wms_product_sync.xml",
        "views/wms_product_sync.xml",
        "views/stock_picking.xml",
        "views/stock_warehouse.xml",
        "views/attachment_queue_view.xml",
    ],
    "demo": [
        "demo/storage_backend.xml",
    ],
}
