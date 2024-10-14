# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
{
    "name": "Shopfloor Packing Info",
    "summary": "Allows to predefine packing information messages per partner.",
    "version": "14.0.1.2.0",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "depends": ["shopfloor", "sales_team", "stock_picking_partner_note"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_partner_views.xml",
        "views/shopfloor_packing_info_views.xml",
        "views/stock_picking_type_views.xml",
        "views/stock_picking_views.xml",
        "views/menus.xml",
    ],
    "demo": ["demo/shopfloor_packing_info_demo.xml"],
}
