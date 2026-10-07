# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Gtin",
    "summary": """Adds support for GTIN barcode scans in shopfloor.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["shopfloor"],
    "maintainers": ["jbaudoux", "nicolas-delbovier-acsone"],
    "data": [],
    "external_dependencies": {
        "python": [
            # >= 2.3.0 required to use 'GS1Message.parse_hri' method
            # and next version 3.0.0 has been refactored bringing
            # incompatibility issues (to check later).
            "biip==2.3.0"
        ]
    },
    "demo": [],
}
