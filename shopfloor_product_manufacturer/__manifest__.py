# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# Copyright 2020 BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor Product Manufacturer",
    "summary": "Show product manufacturer in shopfloor",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, BCIM, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux", "simahawk", "sebalix", "mmequignon", "TDu"],
    "license": "AGPL-3",
    "application": True,
    "depends": [
        "shopfloor",
        #  OCA / product-attribute
        "product_manufacturer",
    ],
    "auto_install": True,
    "installable": True,
}
