# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Delivery carrier preference dangerous goods",
    "summary": "Consider dangerous goods in preferred carrier selection",
    "version": "13.0.1.1.0",
    "development_status": "Alpha",
    "category": "Operations/Inventory/Delivery",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": True,
    "depends": [
        "delivery_carrier_preference",
        "delivery_carrier_dangerous_goods_warning",
    ],
}
