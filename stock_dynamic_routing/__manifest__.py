# Copyright 2019 Camptocamp (https://www.camptocamp.com)
{
    "name": "Stock Dynamic Routing",
    "summary": "Dynamic routing of stock moves",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "category": "Warehouse Management",
    "version": "13.0.1.0.2",
    "license": "AGPL-3",
    "depends": ["stock"],
    "demo": [
        "demo/stock_location_demo.xml",
        "demo/stock_picking_type_demo.xml",
        "demo/stock_routing_demo.xml",
    ],
    "data": ["views/stock_routing_views.xml", "security/ir.model.access.csv"],
    "installable": False,
    "development_status": "Beta",
}
