# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Shipment Advice Toursolver",
    "summary": """
        Use TourSolver to plan shipment advices for ready and released pickings""",
    "version": "16.0.1.1.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel_shipment_advice",
        "shipment_advice_planner_toursolver",
    ],
    "data": ["views/toursolver_task.xml", "views/stock_release_channel.xml"],
    "demo": [],
}
