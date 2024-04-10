# Copyright 2024 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor Vendor Packaging",
    "summary": "Manage shopfloor behavior for vendor packaging",
    "version": "14.0.1.0.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "data": [
        "views/shopfloor_menu.xml",
    ],
    "depends": ["shopfloor", "product_packaging_type_vendor"],
    "auto-install": True,
}
