# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Shipment Advice Process End Time",
    "summary": """This module allows to set a delay time (in minutes) between the
    release channel process end time and the shipment advice arrival to the dock time.
    """,
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel_shipment_advice",
        "stock_release_channel_process_end_time",
    ],
    "data": [
        "views/stock_release_channel.xml",
        "views/stock_warehouse.xml",
    ],
    "demo": [],
}
