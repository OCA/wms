# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Partner Delivery Window",
    "summary": """
        Allows to define an end date (and time) on a release channel and
        propagate it to the concerned pickings""",
    "version": "16.0.2.1.0",
    "license": "AGPL-3",
    "maintainers": ["jbaudoux"],
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_partner_delivery_window",
        "stock_release_channel_shipment_lead_time",
    ],
    "data": [
        "views/stock_release_channel_view.xml",
    ],
}
