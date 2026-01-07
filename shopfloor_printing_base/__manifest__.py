# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Shopfloor Printing Base",
    "summary": """This module allows to provide base method to send printings""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["rousseldenis"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "shopfloor_base",
        "shopfloor_mobile_base",
        "base_report_to_label_printer",
    ],
    "data": [
        "views/shopfloor_menu.xml",
    ],
}
