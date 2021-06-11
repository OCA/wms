# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Stock Storage Type Buffers",
    "summary": "Exclude storage locations from put-away if their buffer is full",
    "version": "13.0.1.3.0",
    "development_status": "Alpha",
    "category": "Warehouse Management",
    "website": "https://github.com/OCA/wms",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["stock_storage_type"],
    "data": [
        "views/stock_location_storage_buffer_views.xml",
        "templates/stock_location_storage_buffer_templates.xml",
        "security/ir.model.access.csv",
    ],
}
