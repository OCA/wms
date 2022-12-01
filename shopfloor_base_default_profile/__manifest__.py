{
    "name": "Shopfloor Base - Default Profile",
    "summary": "Adds a default profile mechanism for shopfloor",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "depends": ["shopfloor_base", "shopfloor_mobile_base"],
    "author": "Brian McMaster, Odoo Community Association (OCA)",
    "maintainers": ["brian10048"],
    "website": "https://github.com/OCA/wms",
    "category": "Inventory",
    "license": "AGPL-3",
    "installable": True,
    "data": [
        "security/ir.model.access.csv",
        "templates/assets.xml",
        "views/shopfloor_app.xml",
        "views/res_user.xml",
    ],
}
