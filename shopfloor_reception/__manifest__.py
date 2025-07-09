{
    "name": "Shopfloor Reception",
    "summary": "Reception scenario for shopfloor",
    "version": "16.0.1.4.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon", "JuMiSanAr"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["shopfloor"],
    "external_dependencies": {"python": ["openupgradelib"]},
    "data": [
        "data/shopfloor_scenario_data.xml",
        "views/shopfloor_menu.xml",
    ],
    "demo": [
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_menu_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
