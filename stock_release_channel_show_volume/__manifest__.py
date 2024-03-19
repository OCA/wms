# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Stock Release Channels show Volume",
    "summary": "Display volumes of stock release channels",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "MT-Software, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_picking_volume",
        "stock_release_channel",
    ],
    "data": [
        "views/release_channel.xml",
        "data/decimal_precision.xml",
    ],
    "installable": True,
}
