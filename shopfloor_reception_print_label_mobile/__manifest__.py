# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Reception Print Label Mobile",
    "summary": """This module allows to show print button at the end of repcetion scenario""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "shopfloor_mobile_printing_base",
        "shopfloor_reception_mobile",
        "shopfloor_reception_print_label",
    ],
    "data": ["templates/assets.xml"],
}
