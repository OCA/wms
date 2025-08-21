# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Available To Promise Auto Unrelease",
    "summary": """Un release released operations no more available to promise""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_available_to_promise_release",
        "queue_job",
    ],
    "data": [
        "data/queue_job_function.xml",
        "views/stock_picking_type.xml",
    ],
    "demo": [],
}
