import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-wms",
    description="Meta package for oca-wms Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-delivery_carrier_warehouse>=16.0dev,<16.1dev',
        'odoo-addon-sale_stock_available_to_promise_release>=16.0dev,<16.1dev',
        'odoo-addon-sale_stock_available_to_promise_release_block>=16.0dev,<16.1dev',
        'odoo-addon-shopfloor_base>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_to_promise_release>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_to_promise_release_block>=16.0dev,<16.1dev',
        'odoo-addon-stock_available_to_promise_release_exclude_location>=16.0dev,<16.1dev',
        'odoo-addon-stock_dynamic_routing>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_completion_info>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_type_shipping_policy>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_auto_release>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_batch_mode_commercial_partner>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_cutoff>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_delivery>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_geoengine>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_partner_delivery_window>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_partner_public_holidays>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_plan>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_plan_process_end_time>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_process_end_time>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_propagate_channel_picking>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_shipment_advice>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_shipment_advice_process_end_time>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_shipment_advice_toursolver>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_shipment_lead_time>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_show_volume>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_show_weight>=16.0dev,<16.1dev',
        'odoo-addon-stock_storage_type>=16.0dev,<16.1dev',
        'odoo-addon-stock_storage_type_putaway_abc>=16.0dev,<16.1dev',
        'odoo-addon-stock_warehouse_flow>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
