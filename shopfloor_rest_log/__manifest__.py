# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor REST log",
    "summary": "Integrate rest_log into Shopfloor app",
    "version": "14.0.1.1.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "ACSONE, Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "license": "LGPL-3",
    "depends": ["rest_log", "shopfloor_base"],
    "data": ["security/groups.xml", "views/menus.xml", "views/shopfloor_app.xml"],
    "post_init_hook": "post_init_hook",
}
