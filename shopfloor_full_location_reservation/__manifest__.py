# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Shopfloor full location reservation",
    "summary": (
        "Adds a configuration to the shopfloor scenario "
        "which allows to trigger the stock full location reservation"
    ),
    "author": "MT Software, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "shopfloor",
        "stock_full_location_reservation",
    ],
    "data": [
        "views/shopfloor_menu.xml",
    ],
    "auto_install": True,
    "post_init_hook": "post_init_hook",
    "maintainers": ["mt-software-de"],
}
