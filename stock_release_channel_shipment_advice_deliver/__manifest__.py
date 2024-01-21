# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Shipment Advice Deliver",
    "summary": """This module adds an action to the release channel to
    automate the delivery of its shippings.""",
    "author": "ACSONE SA/NV, BCIM, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "stock_release_channel",
        "queue_job",
        "stock_release_channel_shipment_advice",
        "web_notify",
        "stock_available_to_promise_release",
    ],
    "data": [
        "security/stock_release_channel_deliver_check_wizard.xml",
        "wizards/stock_release_channel_deliver_check_wizard.xml",
        "data/queue_job_channel.xml",
        "data/queue_job_function.xml",
        "views/stock_release_channel.xml",
    ],
}
