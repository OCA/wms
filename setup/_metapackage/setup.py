import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-wms",
    description="Meta package for oca-wms Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-delivery_carrier_warehouse',
        'odoo14-addon-shopfloor',
        'odoo14-addon-shopfloor_base',
        'odoo14-addon-shopfloor_mobile',
        'odoo14-addon-shopfloor_mobile_base',
        'odoo14-addon-stock_picking_completion_info',
        'odoo14-addon-stock_picking_consolidation_priority',
        'odoo14-addon-stock_storage_type',
        'odoo14-addon-stock_storage_type_buffer',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
