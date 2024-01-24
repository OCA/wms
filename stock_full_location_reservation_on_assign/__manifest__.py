# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
{
    "name": "Stock full location reservation on assign",
    "summary": "Do a automatic full location reservation" "on picking's action_assign",
    "author": "MT Software, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["stock_full_location_reservation"],
    "data": [
        "views/stock_picking_type_views.xml",
    ],
    "maintainers": ["mt-software-de"],
}
