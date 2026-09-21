# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Single Product Transfer Full Reservation",
    "summary": """Adds a configuration to the single product transfer "
    "scenario which allows to trigger the full reservation of product "
    "available at location for the selected lot/packaging""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "maintainers": ["lmignon"],
    "depends": [
        "shopfloor_single_product_transfer",
        "shopfloor_full_location_reservation",
    ],
    "post_init_hook": "post_init_hook",
}
