# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Shopfloor - Checkout Package Measurement",
    "summary": "Add a screen on checkout scenario for required package measurements.",
    "version": "14.0.1.2.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["TDu"],
    "license": "AGPL-3",
    "depends": [
        # OCA/wms
        "shopfloor",
        # OCA/delivery-carrier
        "delivery_carrier_package_measure_required",
    ],
    "installable": True,
}
