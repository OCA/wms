# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel - Block Sale Delivery",
    "summary": """
        Block delivery when the unavailability has been announced on the sale order.
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, BCIM, Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        # core
        "sale_stock",
        # OCA/wms
        "stock_release_channel_block_backorder",
    ],
    "data": ["views/sale_order.xml"],
    "installable": True,
}
