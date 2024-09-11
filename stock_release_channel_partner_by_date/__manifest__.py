# Copyright 2024 Camptocamp
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Stock Release Channels for Delivery Dates",
    "summary": "Set release channels for specific delivery dates",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["sebalix", "jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel",
    ],
    "data": [
        "views/res_partner.xml",
        "security/stock_release_channel_partner_date.xml",
    ],
    "installable": True,
}
