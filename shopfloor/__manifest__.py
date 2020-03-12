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
    "depends": [
        "stock",
        "stock_picking_batch",
        "base_rest",
        "auth_api_key",
        # https://github.com/OCA/stock-logistics-warehouse/pull/808
        "stock_picking_completion_info",
        # https://github.com/OCA/wms/pull/12
        "stock_storage_type",
        # https://github.com/OCA/wms/pull/13
        "stock_storage_type_putaway_strategy",
        # https://github.com/OCA/stock-logistics-warehouse/pull/855
        "stock_location_children",
        # https://github.com/OCA/stock-logistics-workflow/pull/608
        "stock_quant_package_dimension",
        # https://github.com/OCA/stock-logistics-workflow/pull/607
        "stock_quant_package_product_packaging",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/shopfloor_operation_group.xml",
        "views/shopfloor_menu.xml",
        "views/shopfloor_process.xml",
        "views/stock_picking_type.xml",
        "views/stock_location.xml",
        "views/shopfloor_profile_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/auth_api_key_demo.xml",
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_process_demo.xml",
        "demo/shopfloor_menu_demo.xml",
        "demo/shopfloor_operation_group_demo.xml",
        "demo/shopfloor_profile_demo.xml",
    ],
}
