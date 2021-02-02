# Copyright 2020 Camptocamp (https://www.camptocamp.com)
{
    "name": "Shopfloor - Checkout Sync",
    "summary": "Glue module",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "maintainers": ["guewen"],
    "depends": [
        "shopfloor",
        # OCA/stock-logistics-warehouse
        "stock_checkout_sync",
    ],
    "auto_install": True,
    "installable": True,
}
