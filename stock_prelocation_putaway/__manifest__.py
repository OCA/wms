# Copyright 2020 <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Pre-location Putaway",
    "summary": "Pre sort goods in dedicated location",
    "version": "14.0.1.0.0",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": True,
    "maintainers": ["hparfr"],
    "depends": ["stock_putaway_hook", "stock_location_children"],
    "data": ["views/stock_location.xml"],
    "demo": ["demo/stock_location.xml"],
}
