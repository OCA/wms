# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Delivery Carrier Preference",
    "summary": "Advanced selection of preferred shipping methods",
    "version": "14.0.1.1.2",
    "category": "Operations/Inventory/Delivery",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery",
        "product_total_weight_from_packaging",
        "sale_stock_available_to_promise_release",
        "stock_picking_group_by_partner_by_carrier",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/delivery_carrier_preference.xml",
        "views/stock_move.xml",
        "views/stock_picking.xml",
        "views/stock_location_route.xml",
    ],
}
