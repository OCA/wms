# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Shopfloor Workstation Label Printer",
    "summary": "Adds a label printer configuration to the shopfloor workstation.",
    "version": "14.0.1.0.0",
    "category": "Tools",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/wms",
    "development_status": "Alpha",
    "license": "AGPL-3",
    "depends": ["base_report_to_printer_label", "shopfloor_workstation"],
    "data": ["views/shopfloor_workstation.xml"],
    "installable": True,
}
