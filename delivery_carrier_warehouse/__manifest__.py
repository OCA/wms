# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Delivery Carrier Warehouse",
    "summary": "Get delivery method used in sales orders from warehouse",
    "version": "13.0.1.2.0",
    "category": "Operations/Inventory/Delivery",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery"],
    "data": ["views/stock_warehouse.xml"],
}
