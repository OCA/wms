# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Stock Release Channel Preparation Plan",
    "summary": "Manage release channel preparation plan",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV,BCIM,Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": ["stock_release_channel"],
    "data": [
        "security/stock_release_channel_preparation_plan.xml",
        "security/stock_release_channel_plan_launch.xml",
        "wizards/launch_plan.xml",
        "views/stock_release_channel_preparation_plan.xml",
        "views/stock_release_channel.xml",
    ],
    "demo": [
        "demo/stock_release_channel.xml",
        "demo/stock_release_channel_preparation_plan.xml",
    ],
}
