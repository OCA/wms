# Copyright 2024 Foodles (http://www.foodles.co).
# @author Pierre Verkest <pierreverkest84@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock service level",
    "summary": "Manage stock route by service level",
    "version": "14.0.1.0.1",
    "development_status": "Beta",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Pierre Verkest <pierreverkest84@gmail.com>, Odoo Community Association (OCA)",
    "maintainers": ["petrus-v"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/stock_picking_views.xml",
        "views/stock_service_level.xml",
    ],
}
