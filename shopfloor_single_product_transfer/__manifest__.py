{
    "name": "Shopfloor Single Product Transfer",
    "summary": "Move an item from one location to another.",
    "version": "14.0.1.0.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon"],
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
}
