{
    "name": "Shopfloor Reception Packaging Dimension",
    "summary": "Collect Packaging Dimension from the Reception scenario",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["TDu"],
    "license": "AGPL-3",
    "installable": True,
    "depends": ["shopfloor_reception"],
    "data": ["views/shopfloor_menu.xml"],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
