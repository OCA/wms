# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020 BCIM
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Shopfloor Base",
    "summary": "Core module for creating mobile apps",
    "version": "14.0.2.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["guewen", "simahawk", "sebalix"],
    "license": "LGPL-3",
    "application": True,
    "depends": [
        "base_jsonify",
        "base_rest",
        "base_sparse_field",
        "endpoint_route_handler",
    ],
    "data": [
        "data/module_category_data.xml",
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/shopfloor_app.xml",
        "views/shopfloor_menu.xml",
        "views/shopfloor_scenario_views.xml",
        "views/shopfloor_profile_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/res_users_demo.xml",
        "demo/shopfloor_scenario_demo.xml",
        "demo/shopfloor_menu_demo.xml",
        "demo/shopfloor_profile_demo.xml",
    ],
}
