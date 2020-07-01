# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Sale Delivery Carrier Preference",
    "summary": "Select preferred shipping methods for a sale order",
    "version": "13.0.1.0.0",
    "category": "Operations/Inventory/Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery"],
    "data": ["security/ir.model.access.csv", "views/delivery_carrier_preference.xml"],
}
