# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Shopfloor Workstation",
    "summary": "Manage warehouse workstation with barcode scanners",
    "version": "13.0.1.1.1",
    "development_status": "Alpha",
    "category": "Inventory",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "depends": ["shopfloor", "base_report_to_printer"],
    "demo": ["demo/shopfloor_workstation_demo.xml"],
    "data": ["security/ir.model.access.csv", "views/shopfloor_workstation.xml"],
}
