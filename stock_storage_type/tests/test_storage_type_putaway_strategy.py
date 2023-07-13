# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestPutawayStorageTypeStrategy(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.areas.write({"pack_putaway_strategy": "ordered_locations"})

    def test_storage_strategy_ordered_locations_cardboxes(self):
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product.id,
                            "product_uom_qty": 8.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 4.0
        first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_cardbox_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 4.0
        second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_cardbox_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.move_dest_ids.picking_id
        int_picking.action_assign()  # TODO drop ?
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.cardboxes_bin_1_location,
        )
        # Archive all leaf locations. Ensure that the intermediate location is
        # not returned as a valid leaf location and that the next location in
        # the sequence (reserve) is selected
        int_picking.do_unreserve()
        cardboxes_stock = self.env.ref("stock_storage_type.stock_location_cardboxes")
        cardboxes_stock.child_ids.write({"active": False})
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        reserve_cardbox = self.env.ref(
            "stock_storage_type.stock_location_cardboxes_reserve_bin_1"
        )
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"), reserve_cardbox
        )

    def test_storage_strategy_only_empty_ordered_locations_pallets(self):
        # Set pallets location type as only empty
        self.pallets_location_storage_type.write({"allow_new_product": "empty"})
        # Set a quantity in pallet bin 2 to make sure constraint is applied
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.pallets_bin_2_location, 1.0
        )
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product.id,
                            "product_uom_qty": 96.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 48.0
        first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_pallet_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        # First move line goes into pallets bin 1
        # Second move line goes into pallets bin 3 as bin 1 is planned for
        # first move line and bin 2 is already used
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_3_location,
        )

    def test_storage_strategy_max_weight_ordered_locations_pallets(self):
        # Add a category for max_weight 50
        category_50 = self.env["stock.storage.category"].create(
            {"name": "Pallets max 50 kg", "max_weight": 50}
        )

        # Define new pallets location type with a max weight on bin 2
        light_location_storage_type = self.pallets_location_storage_type.copy(
            {"allow_new_product": "empty", "storage_category_id": category_50.id}
        )
        self.pallets_bin_2_location.write({"storage_category_id": category_50.id})
        self.assertEqual(
            self.pallets_bin_2_location.storage_category_id.capacity_ids,
            light_location_storage_type,
        )
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product.id,
                            "product_uom_qty": 96.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 48.0
        first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        first_package.onchange_product_packaging_id()
        self.assertEqual(first_package.pack_weight, 60)
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_pallet_product_packaging
        second_pack.onchange_product_packaging_id()
        self.assertEqual(second_pack.pack_weight, 60)
        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        # First move line goes into pallets bin 1
        # Second move line goes into pallets bin 3 as bin 1 is planned for
        # first move line and bin 2 is already used
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_3_location,
        )

    def test_storage_strategy_no_products_lots_mix_ordered_locations_cardboxes(self):
        self.cardboxes_location_storage_type.write({"allow_new_product": "same_lot"})
        # Set a quantity in cardbox bin 2 to make sure constraint is applied
        self.env["stock.quant"]._update_available_quantity(
            self.env.ref("product.product_product_10"),
            self.cardboxes_bin_2_location,
            1.0,
        )
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product.id,
                            "product_uom_qty": 8.0,
                            "product_uom": self.product.uom_id.id,
                            "picking_type_id": self.receipts_picking_type.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self.product_lot.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product_lot.id,
                            "product_uom_qty": 10.0,
                            "product_uom": self.product_lot.uom_id.id,
                            "picking_type_id": self.receipts_picking_type.id,
                        },
                    ),
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack product
        in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        ).qty_done = 4.0
        product_first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        product_first_package.product_packaging_id = (
            self.product_cardbox_product_packaging
        )
        # Put in pack product again
        product_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product
        )
        product_ml_without_package.qty_done = 4.0
        product_second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        product_second_pack.product_packaging_id = (
            self.product_cardbox_product_packaging
        )

        # Put in pack product lot
        product_lot_ml = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product_lot
        )
        product_lot_ml.write({"qty_done": 5.0, "lot_name": "A0001"})
        product_lot_first_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        product_lot_first_pack.product_packaging_id = (
            self.product_lot_cardbox_product_packaging
        )
        # Put in pack product lot again
        product_lot_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product_lot
        )
        product_lot_ml_without_package.write({"qty_done": 5.0, "lot_name": "A0002"})
        product_lot_second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        product_lot_second_pack.product_packaging_id = (
            self.product_lot_cardbox_product_packaging
        )

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.mapped("move_dest_ids.picking_id")
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        product_mls = int_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        )
        self.assertEqual(
            product_mls.mapped("location_dest_id"), self.cardboxes_bin_1_location
        )
        product_lot_mls = int_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_lot
        )
        self.assertEqual(
            product_lot_mls.mapped("location_dest_id"),
            self.cardboxes_bin_3_location | self.cardboxes_bin_4_location,
        )

    def test_storage_strategy_none_in_sequence(self):
        """When a location has a strategy 'none' in sequence, stop

        We can use it to stop computing the put-away when the destination
        location match, for instance to use a setup with a sequence:

        1. Stock: None
        2. Stock/Cardboxes Reserve: ordered locations

        If a move is created with destination 'Cardboxes Reserve', the put-away
        rule stops at the rule 1. so the move stays in 'Cardboxes Reserve.
        Then, the destination is changed to 'Stock/Cardboxes Reserve' and
        a recomputation is done, the put-away for Bin 1 is applied.

        """
        move = self._create_single_move(self.product)
        # move.location_dest_id = self.cardboxes_location.id
        move._assign_picking()
        package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.product_lot_cardbox_product_packaging.id}
        )
        self._update_qty_in_location(
            move.location_id, move.product_id, move.product_qty, package=package
        )

        # configure a new sequence with none in the parent location
        self.cardboxes_package_storage_type.storage_location_sequence_ids.unlink()
        self.warehouse.lot_stock_id.pack_putaway_strategy = "none"
        self.warehouse.lot_stock_id.storage_category_id = (
            self.cardboxes_location_storage_type.storage_category_id
        )
        self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "sequence": 1,
            }
        )
        self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.cardboxes_location.id,
                "sequence": 2,
            }
        )

        move._action_assign()
        move_line = move.move_line_ids
        package_level = move_line.package_level_id

        self.assertEqual(
            package_level.location_dest_id,
            self.warehouse.lot_stock_id,
            "the move line's destination must stay in Stock as we have"
            " a 'none' strategy on it and it is in the sequence",
        )

        package_level.location_dest_id = self.cardboxes_location
        # if we reapply the strategy, it should now apply the ordered
        # location of the cardbox location
        package_level.recompute_pack_putaway()

        self.assertTrue(
            package_level.location_dest_id in self.cardboxes_location.child_ids
        )

    def test_storage_strategy_do_not_mix_products_reuse_location(self):
        """Location with restriction 'do_not_mix_products' should have priority

        When locations are configured with 'do_not_mix_products' the strategy
        must give priority to location that already contains the product
        (less qty first).
        """
        StockLocation = self.env["stock.location"]
        self.cardboxes_location_storage_type.write({"allow_new_product": "same"})
        product = self.product
        packaging = self.product_cardbox_product_packaging
        dest_location = self.cardboxes_location
        package = self.env["stock.quant.package"].create(
            {"name": "TEST1", "product_packaging_id": packaging.id}
        )
        self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "package_id": package.id,
                "location_id": self.input_location.id,
            }
        )

        location = StockLocation._get_package_type_putaway_strategy(
            dest_location, package, product, 1.0
        )

        # No location with given product -> the first bin should be returned
        self.assertEqual(location, self.cardboxes_bin_1_location)

        # Set a quantity in cardbox bin 4 to trigger the priority on the
        # location that already contains the product
        self.env["stock.quant"]._update_available_quantity(
            product,
            self.cardboxes_bin_3_location,
            10.0,
        )
        location = StockLocation._get_package_type_putaway_strategy(
            dest_location, package, product, 1.0
        )
        self.assertEqual(location, self.cardboxes_bin_3_location)

        # Set less quantity on bin 4. Since it's the location with less quantity
        # that should have priority
        self.env["stock.quant"]._update_available_quantity(
            product,
            self.cardboxes_bin_4_location,
            1.0,
        )
        location = StockLocation._get_package_type_putaway_strategy(
            dest_location, package, product, 1.0
        )
        self.assertEqual(location, self.cardboxes_bin_4_location)

    def test_storage_strategy_none_in_sequence_to_fixes(self):
        """When a location has a strategy 'none' in sequence, stop

        We can use it to stop computing the put-away when the destination
        location match, In such a case, if the location match and a putaway
        rule is defined on the product for this destination location,
        the location destination will be the location from the putaway rule.

        This is very usefull to support fixed location putaway

        Ex:
        product putaway:
        * in: Cardboxes
        * out: cardboxes_bin_4_location

        sequence:
        1. Stock/Cardboxes: None

        If a move is created with destination "Stock", the put-away rule stops
        at sequence 1. Since a put away exists on the product for 'Cardboxes',
        the product putaway is applied and the final destination is
        'cardboxes_bin_4_location'

        """
        move = self._create_single_move(self.product)
        move._assign_picking()
        self.assertEqual(move.location_dest_id, self.stock_location)
        package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.product_lot_cardbox_product_packaging.id}
        )
        self._update_qty_in_location(
            move.location_id, move.product_id, move.product_qty, package=package
        )

        # configure a new sequence with none in the parent location
        self.cardboxes_package_storage_type.storage_location_sequence_ids.unlink()
        self.cardboxes_location.pack_putaway_strategy = "none"
        self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.cardboxes_location.id,
                "sequence": 1,
            }
        )

        # create a put away rule on the product from cardboxes to bin 4
        self.env["stock.putaway.rule"].create(
            {
                "location_in_id": self.cardboxes_location.id,
                "location_out_id": self.cardboxes_bin_4_location.id,
                "product_id": self.product.id,
            }
        )

        move._action_assign()
        move_line = move.move_line_ids
        package_level = move_line.package_level_id

        self.assertEqual(
            package_level.location_dest_id,
            self.cardboxes_bin_4_location,
        )

    def test_storage_strategy_sequence_condition(self):
        """If a condition is not met on storage location sequence, it's ignored"""
        move = self._create_single_move(self.product)
        move._assign_picking()
        original_location_dest = move.location_dest_id
        package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.product_lot_cardbox_product_packaging.id}
        )
        self._update_qty_in_location(
            move.location_id, move.product_id, move.product_qty, package=package
        )

        # configure a new sequence with none in the parent location
        self.cardboxes_package_storage_type.storage_location_sequence_ids.unlink()
        self.warehouse.lot_stock_id.pack_putaway_strategy = "none"
        self.warehouse.lot_stock_id.storage_category_id = (
            self.cardboxes_location_storage_type.storage_category_id
        )
        condition = self.env["stock.storage.location.sequence.cond"].create(
            {"name": "Always False", "code_snippet": "result = False"}
        )
        self.none_sequence = self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "sequence": 1,
                "location_sequence_cond_ids": [(6, 0, condition.ids)],
            }
        )
        self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.cardboxes_location.id,
                "sequence": 2,
            }
        )

        move._action_assign()
        move_line = move.move_line_ids
        package_level = move_line.package_level_id

        self.assertIn(
            package_level.location_dest_id,
            self.cardboxes_location.child_ids,
            "the move line's destination must go into the cardbox location"
            " since the the first sequence is ignored due to the False"
            " condition on it",
        )

        # if we update the condition to always be True, reset the
        # location_dest on the package_level and reapply the put away strategy
        # the move line's destination must be in Stock as we have a 'none'
        # strategy the first putaway sequence
        condition.code_snippet = "result = True"
        package_level.location_dest_id = original_location_dest.id
        package_level.recompute_pack_putaway()

        self.assertEqual(
            package_level.location_dest_id,
            self.warehouse.lot_stock_id,
            "the move line's destination must stay in Stock as we have"
            " a 'none' strategy on it and it is in the sequence",
        )

        package_level.location_dest_id = self.cardboxes_location
        # if we reapply the strategy, it should now apply the ordered
        # location of the cardbox location
        package_level.recompute_pack_putaway()

        self.assertTrue(
            package_level.location_dest_id in self.cardboxes_location.child_ids
        )

    def test_default_product_package_type(self):
        # We try to move a product that is not contained in a package
        # but has a default package type
        # Destination location should become Pallet location
        move = self._create_single_move(self.product)
        move._assign_picking()
        original_location_dest = move.location_dest_id
        # Change default product package type
        move.product_id.package_type_id = self.pallets_package_storage_type
        self._update_qty_in_location(
            move.location_id, move.product_id, move.product_qty
        )
        move._action_assign()
        move_line = move.move_line_ids

        self.assertEqual(move_line.location_dest_id, self.pallets_bin_1_location)

        self.assertNotEqual(
            original_location_dest,
            move_line.location_dest_id,
        )

    def test_storage_strategy_ordered_locations_cardboxes_with_new_leaf_putaway(self):
        """
        In this scenario, we check that a storage strategy is well applied
        but, then, check that a standard putaway rule has been applied too.

        Storage rule applied: for Cardboxes
        Putaway rule: From Carboxes bin location 1 to Cardbox leaf 1

        Location Structure:

        Stock
        -- Cardbox Bin
        ----- Cardbox leaf
        """

        # Create the fixed location
        self.fix_location = self.env["stock.location"].create(
            {
                "name": "Cardbox 1 Fixed",
                "location_id": self.cardboxes_bin_1_location.id,
            }
        )

        # Create the putaway rule
        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product.id,
                "location_in_id": self.cardboxes_bin_1_location.id,
                "location_out_id": self.fix_location.id,
            }
        )
        self.cardboxes_bin_1_location.pack_putaway_strategy = "none"

        # Create the sequence for Bin 1

        self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.cardboxes_bin_1_location.id,
                "sequence": 1,
            }
        )

        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product.id,
                            "product_uom_qty": 8.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 4.0
        first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_cardbox_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 4.0
        second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_cardbox_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.move_dest_ids.picking_id
        int_picking.action_assign()  # TODO drop ?
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.fix_location,
        )

    def test_storage_strategy_with_view(self):
        """
        Create a new locations structure:
            - Stock
              - Food (View)
                - Food A (View)
                  - Pallet 1
                  - Pallet 2
                - Food B (View)
                   - Cardbox 1
                   - Cardbox 2

        A storage sequence strategy is set on Food (View) to
        go to Cardboxes (Food B) for package type cardboxes

        A putaway rule is set on Food B to go to Cardbox2 for
        product

        Check the product goes well to Cardbox2
        """
        self.food_view = self.env["stock.location"].create(
            {
                "name": "Food View",
                "location_id": self.warehouse.lot_stock_id.id,
                "usage": "view",
            }
        )

        self.food_pallets = self.env["stock.location"].create(
            {
                "name": "Food A",
                "location_id": self.food_view.id,
                "usage": "view",
            }
        )

        self.food_pallet_1 = self.env["stock.location"].create(
            {
                "name": "Food Pallet 1",
                "location_id": self.food_pallets.id,
            }
        )
        self.food_pallet_2 = self.env["stock.location"].create(
            {
                "name": "Food Pallet 2",
                "location_id": self.food_pallets.id,
            }
        )

        self.food_cardboxes = self.env["stock.location"].create(
            {
                "name": "Food B",
                "location_id": self.food_view.id,
                "storage_category_id": self.env.ref(
                    "stock_storage_type.storage_category_cardboxes"
                ).id,
                "usage": "view",
            }
        )

        self.food_cardbox_1 = self.env["stock.location"].create(
            {
                "name": "Food Cardbox 1",
                "location_id": self.food_cardboxes.id,
            }
        )
        self.food_cardbox_2 = self.env["stock.location"].create(
            {
                "name": "Food Cardbox 2",
                "location_id": self.food_cardboxes.id,
            }
        )

        self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product.id,
                "location_in_id": self.food_cardboxes.id,
                "location_out_id": self.food_cardbox_2.id,
            }
        )

        self.food_view.pack_putaway_strategy = "none"

        self.env["stock.storage.location.sequence"].create(
            {
                "package_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.food_cardboxes.id,
                "sequence": 1,
            }
        )

        move = self._create_single_move(self.product)
        move.location_dest_id = self.food_view
        move._assign_picking()
        package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.product_lot_cardbox_product_packaging.id}
        )
        self._update_qty_in_location(
            move.location_id, move.product_id, move.product_qty, package=package
        )

        move._action_assign()
        move_line = move.move_line_ids
        package_level = move_line.package_level_id

        self.assertEqual(
            package_level.location_dest_id,
            self.food_cardbox_2,
            "the move line's destination must stay in Stock as we have"
            " a 'none' strategy on it and it is in the sequence",
        )
