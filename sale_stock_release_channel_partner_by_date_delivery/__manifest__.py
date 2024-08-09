# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock Release Channels with Sales - Delivery",
    "summary": "Filters channels on sales based on selected carrier.",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        # OCA/wms
        "sale_stock_release_channel_partner_by_date",
        "stock_release_channel_delivery",
    ],
    "data": [
        "views/sale_order.xml",
    ],
    "installable": True,
    "auto_install": True,
}
