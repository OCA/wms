# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Reception Print Label",
    "summary": """This module allows to print labels during reception flow""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "base_report_to_label_printer",
        "shopfloor_reception",
        "shopfloor_printing_base",
    ],
    "data": ["views/shopfloor_menu.xml"],
}
