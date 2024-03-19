# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Shipment Advice",
    "summary": """Plan shipment advices for ready and released pickings""",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,BCIM,Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": ["shipment_advice_planner", "stock_release_channel"],
    "data": [
        "wizards/shipment_advice_planner.xml",
        "views/shipment_advice.xml",
        "views/stock_release_channel.xml",
    ],
}
