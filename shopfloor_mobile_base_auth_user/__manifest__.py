# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor Mobile Base auth via user auth",
    "summary": "Provides authentication via standard user login",
    "version": "14.0.1.1.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainer": ["simahawk"],
    "license": "AGPL-3",
    "depends": ["shopfloor_mobile_base", "base_rest_auth_user_service"],
    "data": [
        "demo/shopfloor_app_demo.xml",
        "templates/assets.xml",
    ],
}
