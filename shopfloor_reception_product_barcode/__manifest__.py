{
    "name": "Shopfloor Reception Product Barcode",
    "summary": "Collect Product Barcode from the Reception scenario",
    "version": "16.0.1.2.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["rousseldenis"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "shopfloor_reception",
    ],
    "data": ["views/shopfloor_menu.xml"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
