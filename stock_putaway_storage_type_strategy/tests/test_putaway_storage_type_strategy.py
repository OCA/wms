# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import SavepointCase


class TestPutawayStorageTypeStrategy(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        ref = cls.env.ref
        cls.warehouse = ref('stock.warehouse0')
        # set two steps reception on warehouse
        cls.warehouse.reception_steps = 'two_steps'

        cls.suppliers_location = ref('stock.stock_location_suppliers')
        cls.input_location = ref('stock.stock_location_company')
        cls.stock_location = ref('stock.stock_location_stock')

        cls.cardboxes_location = ref(
            'stock_storage_type.stock_location_cardboxes'
        )
        cls.pallets_location = ref(
            'stock_storage_type.stock_location_pallets'
        )
        cls.putaway_locations = cls.cardboxes_location | cls.pallets_location

        cls.cardboxes_bin_1_location = ref(
            'stock_storage_type.stock_location_cardboxes_bin_1'
        )
        cls.cardboxes_bin_2_location = ref(
            'stock_storage_type.stock_location_cardboxes_bin_2'
        )
        cls.cardboxes_bin_3_location = ref(
            'stock_storage_type.stock_location_cardboxes_bin_3'
        )
        cls.cardboxes_bin_4_location = cls.cardboxes_bin_1_location.copy(
            {'name': 'Bin 4'}
        )
        cls.pallets_bin_1_location = ref(
            'stock_storage_type.stock_location_pallets_bin_1'
        )
        cls.pallets_bin_2_location = ref(
            'stock_storage_type.stock_location_pallets_bin_2'
        )
        cls.pallets_bin_3_location = ref(
            'stock_storage_type.stock_location_pallets_bin_3'
        )

        cls.receipts_picking_type = ref('stock.picking_type_in')
        cls.internal_picking_type = ref('stock.picking_type_internal')

        cls.product = ref('product.product_product_9')
        cls.product_lot = ref('stock.product_cable_management_box')

        cls.cardboxes_package_storage_type = ref(
            'stock_storage_type.package_storage_type_cardboxes')
        cls.pallets_package_storage_type = ref(
            'stock_storage_type.package_storage_type_pallets')
        cls.cardboxes_location_storage_type = ref(
            'stock_storage_type.location_storage_type_cardboxes')
        cls.pallets_location_storage_type = ref(
            'stock_storage_type.location_storage_type_pallets')

        cls.product_cardbox_product_packaging = ref(
            'stock_storage_type.'
            'product_product_9_packaging_4_cardbox'
        )
        cls.product_pallet_product_packaging = ref(
            'stock_storage_type.'
            'product_product_9_packaging_48_pallet'
        )
        cls.product_lot_cardbox_product_packaging = cls.env['product.packaging'].create({
            'name': '5 units cardbox',
            'qty': 5,
            'product_id': cls.product_lot.id,
            'stock_package_storage_type_id': cls.cardboxes_package_storage_type.id,
        })
        cls.product_lot_pallets_product_packaging = cls.env[
            'product.packaging'].create({
                'name': '20 units pallet',
                'qty': 20,
                'product_id': cls.product_lot.id,
                'stock_package_storage_type_id': cls.pallets_package_storage_type.id,
            })

        cls.product_pallets_putaway = ref(
            'stock_putaway_storage_type_strategy.stock_putaway_rule_product_9_stock_pallets'
        )
        cls.product_cardboxes_putaway = ref(
            'stock_putaway_storage_type_strategy.stock_putaway_rule_product_9_stock_cardboxes'
        )
        cls.product_lot_pallets_putaway = cls.product_pallets_putaway.copy(
            {'product_id': cls.product_lot.id}
        )
        cls.product_lot_cardboxes_putaway = cls.product_cardboxes_putaway.copy(
            {'product_id': cls.product_lot.id}
        )
        # pick_types = cls.cls.receipts_picking_type | cls.internal_picking_type
        # pick_types.write({'show_entire_packs': True})

    def test_storage_strategy_ordered_locations_cardboxes(self):
        self.putaway_locations.write({'pack_storage_strategy': 'ordered_locations'})
        # Create picking
        in_picking = self.env['stock.picking'].create({
            'picking_type_id': self.receipts_picking_type.id,
            'location_id': self.suppliers_location.id,
            'location_dest_id': self.input_location.id,
            'move_lines': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 8.0,
                'product_uom': self.product.uom_id.id,
            })],
        })
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 4.0
        first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.packaging_id = self.product_cardbox_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id)
        ml_without_package.qty_done = 4.0
        second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.packaging_id = self.product_cardbox_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.move_dest_ids.picking_id
        int_picking.action_assign()  # TODO drop ?
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(int_picking.move_lines.mapped('location_dest_id'),
                         self.stock_location)
        self.assertEqual(
            int_picking.move_line_ids.mapped('location_dest_id'),
            self.cardboxes_bin_1_location
        )

    def test_storage_strategy_only_empty_ordered_locations_pallets(self):
        self.putaway_locations.write({'pack_storage_strategy': 'ordered_locations'})
        # Set pallets location type as only empty
        self.pallets_location_storage_type.write({'only_empty': True})
        # Set a quantity in pallet bin 2 to make sure constraint is applied
        self.env['stock.quant']._update_available_quantity(
            self.product, self.pallets_bin_2_location, 1.0
        )
        # Create picking
        in_picking = self.env['stock.picking'].create({
            'picking_type_id': self.receipts_picking_type.id,
            'location_id': self.suppliers_location.id,
            'location_dest_id': self.input_location.id,
            'move_lines': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 96.0,
                'product_uom': self.product.uom_id.id,
            })],
        })
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 48.0
        first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.packaging_id = self.product_pallet_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id)
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.packaging_id = self.product_pallet_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(int_picking.move_lines.mapped('location_dest_id'),
                         self.stock_location)
        # First move line goes into pallets bin 1
        # Second move line goes into pallets bin 3 as bin 1 is planned for
        # first move line and bin 2 is already used
        self.assertEqual(
            int_picking.move_line_ids.mapped('location_dest_id'),
            self.pallets_bin_1_location | self.pallets_bin_3_location
        )

    def test_storage_strategy_no_products_lots_mix_ordered_locations_cardboxes(self):
        self.putaway_locations.write({'pack_storage_strategy': 'ordered_locations'})
        self.cardboxes_location_storage_type.write({
            'do_not_mix_products': True,
            'do_not_mix_lots': True
        })
        # Set a quantity in cardbox bin 2 to make sure constraint is applied
        self.env['stock.quant']._update_available_quantity(
            self.env.ref('product.product_product_10'),
            self.cardboxes_bin_2_location,
            1.0
        )
        # Create picking
        in_picking = self.env['stock.picking'].create({
            'picking_type_id': self.receipts_picking_type.id,
            'location_id': self.suppliers_location.id,
            'location_dest_id': self.input_location.id,
            'move_lines': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom_qty': 8.0,
                'product_uom': self.product.uom_id.id,
                'picking_type_id': self.receipts_picking_type.id,
            }), (0, 0, {
                'name': self.product_lot.name,
                'product_id': self.product_lot.id,
                'product_uom_qty': 10.0,
                'product_uom': self.product_lot.uom_id.id,
                'picking_type_id': self.receipts_picking_type.id,
            })],
        })
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack product
        in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        ).qty_done = 4.0
        product_first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_first_package.packaging_id = self.product_cardbox_product_packaging
        # Put in pack product again
        product_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product
        )
        product_ml_without_package.qty_done = 4.0
        product_second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_second_pack.packaging_id = self.product_cardbox_product_packaging

        # Put in pack product lot
        product_lot_ml = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product_lot
        )
        product_lot_ml.write({'qty_done': 5.0, 'lot_name': 'A0001'})
        product_lot_first_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_lot_first_pack.packaging_id = self.product_lot_cardbox_product_packaging
        # Put in pack product lot again
        product_lot_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product_lot
        )
        product_lot_ml_without_package.write({'qty_done': 5.0, 'lot_name': 'A0002'})
        product_lot_second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_lot_second_pack.packaging_id = self.product_lot_cardbox_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.mapped('move_dest_ids.picking_id')
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(int_picking.move_lines.mapped('location_dest_id'),
                         self.stock_location)
        product_mls = int_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        )
        self.assertEqual(
            product_mls.mapped('location_dest_id'), self.cardboxes_bin_1_location
        )
        product_lot_mls = int_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_lot
        )
        self.assertEqual(
            product_lot_mls.mapped('location_dest_id'),
            self.cardboxes_bin_3_location | self.cardboxes_bin_4_location
        )
