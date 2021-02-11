# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Delivery Preference Glue Stock Picking Group",
    "summary": "Fix Delivery preferences module on grouping picking",
    "version": "13.0.1.0.0",
    "category": "Hidden",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        # OCA/wms
        "delivery_carrier_preference",
        # OCA/stock_logistic_workflow
        "stock_picking_group_by_partner_by_carrier",
    ],
    "website": "https://github.com/OCA/wms",
    "installable": True,
    "auto_install": True,
}
