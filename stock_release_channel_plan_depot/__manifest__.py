# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Release Channel Plan Depot",
    "summary": """This module allows users to set partner depot on
    stock release channel preparation plan.""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "depends": ["stock_depot", "stock_release_channel_plan"],
    "data": [
        "views/stock_release_channel_preparation_plan.xml",
    ],
}
