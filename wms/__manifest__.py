# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'WMS',
    'version': '12.0.1.0.0',
    'summary': 'Warehouse Management System',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Stock Management',
    'depends': [
        'stock',
        'stock_location_zone',
        'stock_location_attribute',
        'stock_location_bin_name',
    ],
    'data': [
        'views/wms_views.xml',
        'views/res_config_settings_views.xml',
        'security/wms_security.xml',
    ],
    'installable': True,
    'license': 'AGPL-3',
    'application': True,
    'development_status': 'Alpha',
}
