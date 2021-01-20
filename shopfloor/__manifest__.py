# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020 BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor",
    "summary": "manage warehouse operations with barcode scanners",
    "version": "13.0.2.0.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["guewen", "simahawk", "sebalix"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        "stock",
        "stock_picking_batch",
        "base_jsonify",
        "base_rest",
        "base_sparse_field",
        "auth_api_key",
        #  OCA / stock-logistics-warehouse
        "stock_picking_completion_info",
        #  OCA / stock-logistics-warehouse
        "stock_quant_package_dimension",
        #  OCA / stock-logistics-warehouse
        "stock_quant_package_product_packaging",
        # TODO: used for manuf info on prod detail.
        # This must be an optional dep
        "product_manufacturer",
        # TODO: used for prod lot expire detail info.
        # This must be an optional dep
        "product_expiry",
        # TODO: used for package.package_storage_type_id detail info.
        # This must be an optional dep
        "stock_storage_type",
        # TODO: used for picking.carrier_id detail info.
        # This must be an optional dep
        "delivery",
        #  OCA / product-attribute
        "product_packaging_type",
    ],
    "data": [
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
        "security/ir.model.access.csv",
        "views/res_partner.xml",
        "views/shopfloor_menu.xml",
        "views/stock_picking_type.xml",
        "views/stock_location.xml",
        "views/stock_move_line.xml",
        "views/stock_picking_views.xml",
        "views/shopfloor_profile_views.xml",
        "views/shopfloor_log_views.xml",
        "views/menus.xml",
    ],
    "demo": [
        "demo/auth_api_key_demo.xml",
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_menu_demo.xml",
        "demo/shopfloor_profile_demo.xml",
    ],
}
