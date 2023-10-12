# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Wms Connector",
    "summary": """
        WMS Connector""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://www.akretion.com",
    "depends": ["stock", "sale", "attachment_synchronize"],
    "data": [
        "security/wms_product_sync.xml",
        "views/wms_product_sync.xml",
        "data/cron.xml",
        "data/ir_filters.xml",
        "views/attachment_queue.xml",
        "views/stock_picking.xml",
        "views/product_product.xml",
        "views/stock_warehouse.xml",
    ],
    "demo": [
        "demo/wms_product_sync.xml",
        "demo/attachment_queue.xml",
        "demo/stock_picking.xml",
        "demo/product_product.xml",
        "demo/stock_warehouse.xml",
    ],
}
