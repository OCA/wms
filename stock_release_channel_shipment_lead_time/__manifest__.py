# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Release channel shipment lead time",
    "summary": "Release channel with shipment lead time",
    "version": "16.0.1.0.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, BCIM, Odoo Community Association (OCA)",
    "maintainers": ["jbaudoux"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "stock_release_channel",  # OCA/wms
        "stock_release_channel_process_end_time",  # OCA/wms
        "stock_warehouse_calendar",  # OCA/stock-logistics-warehouse
        "shipment_advice_planner",  # OCA/stock-logistics-transport
    ],
    "data": [
        "views/shipment_advice_views.xml",
        "views/stock_release_channel_views.xml",
    ],
    "installable": True,
}
