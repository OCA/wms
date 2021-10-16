import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo12-addons-oca-wms",
    description="Meta package for oca-wms Odoo addons",
    version=version,
    install_requires=[
        'odoo12-addon-stock_storage_type',
        'odoo12-addon-wms',
        'odoo12-addon-wms_demo',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 12.0',
    ]
)
