# Copyright 2019-2021 Camptocamp SA
# Copyright 2019-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Storage Type",
    "summary": "Manage packages and locations storage types",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux", "rousseldenis"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        # OCA/stock-logistics-tracking
        "stock_quant_package_dimension",
        # OCA/stock-logistics-warehouse
        "stock_storage_category_capacity_name",
        "stock_location_pending_move",
        # OCA/stock-logistics-workflow
        "stock_putaway_hook",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template.xml",
        "views/stock_location.xml",
        "views/stock_storage_category.xml",
        "views/stock_storage_category_allow_new_product_cond.xml",
        "views/stock_package_level.xml",
        "views/stock_package_type.xml",
        "views/stock_storage_location_sequence.xml",
        "views/stock_storage_location_sequence_cond.xml",
        "views/storage_type_menus.xml",
    ],
    "demo": [
        "demo/stock_package_type.xml",
        "demo/stock_storage_category_allow_new_product_cond.xml",
        "demo/stock_storage_category.xml",
        "demo/stock_storage_category_capacity.xml",
        "demo/product_packaging.xml",
        "demo/stock_location.xml",
        "demo/stock_storage_location_sequence.xml",
    ],
}
