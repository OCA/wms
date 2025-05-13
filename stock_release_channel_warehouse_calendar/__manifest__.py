# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
{
    "name": "Stock Release Channels Warehouse Calendar",
    "summary": "Glue module between release channel and warehouse calendar",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "BCIM, Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel",
        "stock_warehouse_calendar",  # OCA/stock-logistics-warehouse
    ],
    "auto_install": True,
}
