{
    "name": "Shopfloor Reception",
    "summary": "Reception scenario for shopfloor",
    "version": "14.0.1.1.1",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, MT Software, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon", "JuMiSanAr"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["shopfloor"],
    "data": [
        "data/shopfloor_scenario_data.xml",
        "views/shopfloor_menu.xml",
    ],
    "demo": [
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_menu_demo.xml",
    ],
}
