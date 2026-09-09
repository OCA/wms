# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Location Content Transfer Print Label Mobile",
    "summary": """Shows a print button to print label during
    location_content_transfer scenario.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "shopfloor_mobile",
        "shopfloor_location_content_transfer_print_label",
        "shopfloor_mobile_printing_base",
    ],
    "data": ["templates/assets.xml"],
    "demo": [],
}
