import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-wms",
    description="Meta package for oca-wms Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-stock_available_to_promise_release>=16.0dev,<16.1dev',
        'odoo-addon-stock_dynamic_routing>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_completion_info>=16.0dev,<16.1dev',
        'odoo-addon-stock_picking_type_shipping_policy>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_auto_release>=16.0dev,<16.1dev',
        'odoo-addon-stock_release_channel_batch_mode_commercial_partner>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
