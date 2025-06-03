# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock release channel plan shipment lead time",
    "summary": "Stock release channel plan shipment lead time",
    "version": "16.0.1.1.0",
    "development_status": "Beta",
    "category": "Uncategorized",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "license": "AGPL-3",
    "depends": [
        "stock_release_channel_plan",
        "stock_release_channel_shipment_lead_time",
    ],
    "data": [
        "views/release_channel.xml",
    ],
    "auto_install": True,
}
