# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Propagate Channel Process End Time",
    "summary": """
        Allows to propagate the channel process end time to every picking that is
        created from the original one.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel_propagate_channel_picking",
        "stock_release_channel_process_end_time",
        "stock_available_to_promise_release",
    ],
    "data": [],
    "demo": [],
}
