{
    "name": "Shopfloor Reception",
    "summary": "Reception scenario for shopfloor",
    "version": "14.0.2.4.0",
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
    ],
    "demo": [
        "demo/stock_picking_type_demo.xml",
        "demo/shopfloor_menu_demo.xml",
    ],
}
