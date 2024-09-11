# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
{
    "name": "Stock Release Channels with Sales",
    "summary": "Release channels integration with Sales",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        # core
        "sales_team",
        "sale_stock",
        # OCA/wms
        "stock_release_channel_partner_by_date",
    ],
    "data": [
        "security/ir_model_access.xml",
        "views/sale_order.xml",
    ],
    "installable": True,
    "auto_install": True,
}
