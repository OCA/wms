{
    "name": "Shopfloor Single Product Transfer",
    "summary": "Move an item from one location to another.",
    "version": "18.0.1.1.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/stock-logistics-shopfloor",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon", "jbaudoux", "TDu"],
    "license": "AGPL-3",
    "installable": True,
    "auto_install": False,
    "depends": ["shopfloor"],
    "data": [
        "data/shopfloor_scenario_data.xml",
    ],
    "demo": [
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_menu_demo.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
