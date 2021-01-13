import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-wms",
    description="Meta package for oca-wms Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-delivery_carrier_preference',
        'odoo13-addon-delivery_carrier_warehouse',
        'odoo13-addon-sale_stock_available_to_promise_release',
        'odoo13-addon-shopfloor',
        'odoo13-addon-shopfloor_batch_automatic_creation',
        'odoo13-addon-shopfloor_checkout_sync',
        'odoo13-addon-shopfloor_mobile',
        'odoo13-addon-shopfloor_mobile_custom_example',
        'odoo13-addon-stock_available_to_promise_release',
        'odoo13-addon-stock_available_to_promise_release_dynamic_routing',
        'odoo13-addon-stock_dynamic_routing',
        'odoo13-addon-stock_move_source_relocate',
        'odoo13-addon-stock_move_source_relocate_dynamic_routing',
        'odoo13-addon-stock_picking_type_shipping_policy',
        'odoo13-addon-stock_picking_type_shipping_policy_group_by',
        'odoo13-addon-stock_reception_screen',
        'odoo13-addon-stock_storage_type',
        'odoo13-addon-stock_storage_type_buffer',
        'odoo13-addon-stock_storage_type_putaway_abc',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
