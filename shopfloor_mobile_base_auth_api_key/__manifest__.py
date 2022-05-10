# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Shopfloor Mobile Base auth via API key",
    "summary": "Provides authentication via API key to Shopfloor base mobile app",
    "version": "14.0.2.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainer": ["simahawk"],
    "license": "LGPL-3",
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
