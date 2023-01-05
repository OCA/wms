# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Stock Release Channels",
    "summary": "Manage workload in WMS with release channels",
    "version": "14.0.1.1.0",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "sale_stock",
        "stock_available_to_promise_release",  # OCA/wms
        "queue_job",  # OCA/queue
    ],
    "data": [
        "views/assets.xml",
        "views/stock_release_channel_views.xml",
        "views/stock_picking_views.xml",
        "data/stock_release_channel_data.xml",
        "data/queue_job_data.xml",
        "data/ir_cron_data.xml",
        "security/stock_release_channel.xml",
    ],
    "installable": True,
}
