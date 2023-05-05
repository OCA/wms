# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Auto Release",
    "summary": """
        Add an automatic release mode to the release channel""",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel",
        "stock_move_auto_assign_auto_release",
    ],
    "data": [
        "data/queue_job_data.xml",
        "views/stock_release_channel.xml",
    ],
    "demo": [],
}
