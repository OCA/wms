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
    "depends": [
        "stock",
        "sale",
        "attachment_synchronize",
    ],
    "data": [
        "views/stock_warehouse.xml",
    ],
    "demo": [
        "demo/stock_warehouse.xml",
    ],
}
