# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor Mobile Base auth via API key",
    "summary": "Provides authentication via API key to Shopfloor base mobile app",
    "version": "14.0.1.1.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainer": ["simahawk"],
    "license": "AGPL-3",
    "depends": [
        "shopfloor_mobile_base",
        "auth_api_key_group",
    ],
    "data": ["templates/assets.xml", "views/shopfloor_app.xml"],
    "demo": [
        "demo/auth_api_key_demo.xml",
        "demo/auth_api_key_group_demo.xml",
        "demo/shopfloor_app_demo.xml",
    ],
}
