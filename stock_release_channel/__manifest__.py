# Copyright 2020 Camptocamp
# License OPL-1

{
    "name": "Stock Release Channels",
    "summary": "Manage workload in WMS with release channels",
    "version": "13.0.1.0.0",
    "license": "OPL-1",
    "author": "Camptocamp",
    "website": "https://www.camptocamp.com",
    "depends": ["sale_stock", "stock_available_to_promise_release", "ddmrp"],
    "data": [
        "security/stock_release_channel.xml",
        "views/stock_release_channel_views.xml",
        "views/stock_picking_views.xml",
        "data/stock_release_channel_data.xml",
    ],
}
