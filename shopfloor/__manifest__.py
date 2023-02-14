# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020 BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor",
    "summary": "manage warehouse operations with barcode scanners",
    "version": "14.0.2.24.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["guewen", "simahawk", "sebalix"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        "shopfloor_base",
        "stock",
        "stock_picking_batch",
        "jsonifier",
        "base_rest",
        "base_sparse_field",
        #  OCA / stock-logistics-warehouse
        "stock_helper",
        "stock_picking_completion_info",
        #  OCA / stock-logistics-workflow
        "stock_quant_package_dimension",
        "stock_quant_package_product_packaging",
        "stock_picking_progress",
        # TODO: used for manuf info on prod detail.
        # This must be an optional dep
        "product_manufacturer",
        # TODO: used for prod lot expire detail info.
        # This must be an optional dep
        "product_expiry",
        # TODO: used for package.package_storage_type_id detail info.
        # This must be an optional dep
        "stock_storage_type",
        # TODO: used for picking.carrier_id detail info
        # and to validate packaging/carrier in checkout scenario
        # This must be an optional dep
        "delivery",
        #  OCA / product-attribute
        "product_packaging_type",
        #  OCA / delivery
        "stock_picking_delivery_link",
    ],
    "data": [
        "data/shopfloor_scenario_data.xml",
        "security/groups.xml",
        "views/shopfloor_menu.xml",
        "views/stock_picking_type.xml",
        "views/stock_location.xml",
        "views/stock_move_line.xml",
    ],
    "demo": [
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_profile_demo.xml",
        "demo/shopfloor_menu_demo.xml",
        "demo/shopfloor_app_demo.xml",
    ],
    "installable": True,
}
