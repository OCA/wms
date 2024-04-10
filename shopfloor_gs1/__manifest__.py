# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor GS1",
    "summary": "Integrate GS1 barcode scan into Shopfloor app",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["simahawk", "sebalix"],
    "license": "AGPL-3",
    "depends": ["shopfloor"],
    "external_dependencies": {
        "python": [
            # >= 2.3.0 required to use 'GS1Message.parse_hri' method
            # and next version 3.0.0 has been refactored bringing
            # incompatibility issues (to check later).
            "biip==2.3.0"
        ]
    },
    "data": [],
}
