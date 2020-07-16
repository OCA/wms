# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "l10n_eu product ADR delivery carrier",
    "summary": "Raise warning according to delivery carrier ADR settings",
    "version": "13.0.1.1.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery", "l10n_eu_product_adr"],
    "data": ["views/delivery_carrier.xml", "wizard/choose_delivery_carrier.xml"],
}
