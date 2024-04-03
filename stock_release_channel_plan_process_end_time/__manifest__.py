# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Plan Process End Time",
    "summary": "Glue module between release channel plan and process end time",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "BCIM,Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel_plan",
        "stock_release_channel_process_end_time",
    ],
    "data": [
        "wizards/launch_plan.xml",
    ],
    "demo": [
        "demo/stock_release_channel.xml",
    ],
    "auto_install": True,
}
