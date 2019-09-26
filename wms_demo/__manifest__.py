# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'WMS - Demo',
    'version': '12.0.1.0.0',
    'summary': 'Warehouse Management System',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Stock Management',
    'depends': [
        'wms',
        'product_expiry',
        'stock_vertical_lift',
        'stock_picking_completion_info',
        'stock_move_location_dest_constraint_empty',
        'stock_move_location_dest_constraint_tag',
        'stock_putaway_rule',
        'stock_putaway_abc',
        'stock_putaway_abc_move_location_dest_constraint',
        'stock_putaway_recursive',
        'stock_picking_type_routing_operation',
        'stock_reserve_rule',
    ],
    'demo': [
        'demo/stock_warehouse_demo.xml',
        'demo/product_storage_tag_demo.xml',
        'demo/picking_type_sequence_demo.xml',
        'demo/stock_location_demo.xml',
        'demo/picking_type_demo.xml',
        'demo/stock_location_bin_demo.xml',
        'demo/stock_location_route_demo.xml',
        'demo/product_product_demo.xml',
        'demo/product_packaging_demo.xml',
        'demo/stock_putaway_rule_demo.xml',
        'demo/stock_reserve_rule_demo.xml',
        'demo/stock_rule_demo.xml',
    ],
    'data': [
    ],
    'installable': True,
    'license': 'AGPL-3',
    'application': False,
    'development_status': 'Alpha',
}
