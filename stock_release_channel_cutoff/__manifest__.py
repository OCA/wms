# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
{
    "name": "Stock Release Channels Cutoff",
    "summary": "Add the cutoff time to the release channel",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": ["stock_release_channel", "stock_release_channel_process_end_time"],
    "data": [
        "views/stock_release_channel_views.xml",
    ],
}
