# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    "name": "Stock Release Channels",
    "summary": "Manage workload in WMS with release channels",
    "version": "16.0.2.0.1",
    "development_status": "Beta",
    "license": "AGPL-3",
    "author": "Camptocamp, ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["sebalix"],
    "website": "https://github.com/OCA/wms",
    "depends": [
        "web",
        "stock_available_to_promise_release",  # OCA/wms
        "queue_job",  # OCA/queue
    ],
    "data": [
        "views/stock_release_channel_views.xml",
        "views/stock_picking_views.xml",
        "data/stock_release_channel_data.xml",
        "data/queue_job_data.xml",
        "data/ir_cron_data.xml",
        "security/stock_release_channel.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_release_channel/static/src/scss/stock_release_channel.scss",
            "stock_release_channel/static/src/js/progressbar_fractional_widget.js",
        ],
    },
    "installable": True,
}
