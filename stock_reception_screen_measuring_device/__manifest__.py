# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
{
    "name": "Stock Measuring Device on Reception Screen",
    "summary": "Allow to use a measuring device from a reception screen."
    "for packaging measurement",
    "version": "13.0.1.0.1",
    "category": "Warehouse",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["stock_reception_screen", "stock_measuring_device"],
    "data": [
        "views/stock_reception_screen_view.xml",
        "views/measuring_device_view.xml",
    ],
    "website": "https://github.com/OCA/wms",
    "installable": True,
    "auto_install": True,
    "development_status": "Alpha",
    "maintainers": ["gurneyalex"],
}
