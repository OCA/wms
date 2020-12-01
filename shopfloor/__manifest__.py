# © 2020 Camptocamp, Akretion, BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor",
    "summary": "manage warehouse operations with barcode scanners",
    "version": "13.0.1.0.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://odoo-community.org",
    "author": "Akretion, BCIM, Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "depends": ["stock", "base_rest", "auth_api_key"],
    "data": [
        "security/ir.model.access.csv",
        "views/shopfloor_operation_group.xml",
        "views/shopfloor_menu.xml",
        "views/shopfloor_process.xml",
        "views/stock_picking_type.xml",
        "views/shopfloor_profile_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/auth_api_key_demo.xml",
        "demo/shopfloor_process_demo.xml",
        "demo/shopfloor_menu_demo.xml",
        "demo/shopfloor_operation_group_demo.xml",
        "demo/shopfloor_profile_demo.xml",
    ],
}
