# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock Release Channels with Sales",
    "summary": "Release channels integration with Sales",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        # core
        "sale_stock",
        # OCA/wms
        "stock_release_channel",
    ],
    "data": [
        "views/sale_order.xml",
    ],
    "installable": True,
    "auto_install": True,
}
