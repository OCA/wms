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
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
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
        first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_cardbox_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 4.0
        second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_cardbox_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.move_dest_ids.picking_id
        int_picking.action_assign()  # TODO drop ?
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_lines.mapped("location_dest_id"), self.stock_location
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
            int_picking.move_lines.mapped("location_dest_id"), self.stock_location
        )
        reserve_cardbox = self.env.ref(
            "stock_storage_type.stock_location_cardboxes_reserve_bin_1"
        )
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"), reserve_cardbox
        )

    def test_storage_strategy_only_empty_ordered_locations_pallets(self):
        # Set pallets location type as only empty
        self.pallets_location_storage_type.write({"only_empty": True})
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
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
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
        first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_pallet_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_lines.mapped("location_dest_id"), self.stock_location
        )
        # First move line goes into pallets bin 1
        # Second move line goes into pallets bin 3 as bin 1 is planned for
        # first move line and bin 2 is already used
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_3_location,
        )

    def test_storage_strategy_max_weight_ordered_locations_pallets(self):
        # Define new pallets location type with a max weight on bin 2
        light_location_storage_type = self.pallets_location_storage_type.copy(
            {"only_empty": True, "max_weight": 50}
        )
        self.pallets_bin_2_location.write(
            {"location_storage_type_ids": [(6, 0, light_location_storage_type.ids)]}
        )
        self.assertEqual(
            self.pallets_bin_2_location.location_storage_type_ids,
            light_location_storage_type,
        )
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
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
        first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        first_package.onchange_product_packaging_id()
        self.assertEqual(first_package.pack_weight, 60)
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_pallet_product_packaging
        second_pack.onchange_product_packaging_id()
        self.assertEqual(second_pack.pack_weight, 60)
        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_lines.mapped("location_dest_id"), self.stock_location
        )
        # First move line goes into pallets bin 1
        # Second move line goes into pallets bin 3 as bin 1 is planned for
        # first move line and bin 2 is already used
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_3_location,
        )

    def test_storage_strategy_no_products_lots_mix_ordered_locations_cardboxes(self):
        self.cardboxes_location_storage_type.write(
            {"do_not_mix_products": True, "do_not_mix_lots": True}
        )
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
                "move_lines": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
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
        product_first_package = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_first_package.product_packaging_id = (
            self.product_cardbox_product_packaging
        )
        # Put in pack product again
        product_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product
        )
        product_ml_without_package.qty_done = 4.0
        product_second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_second_pack.product_packaging_id = (
            self.product_cardbox_product_packaging
        )

        # Put in pack product lot
        product_lot_ml = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product_lot
        )
        product_lot_ml.write({"qty_done": 5.0, "lot_name": "A0001"})
        product_lot_first_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_lot_first_pack.product_packaging_id = (
            self.product_lot_cardbox_product_packaging
        )
        # Put in pack product lot again
        product_lot_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and ml.product_id == self.product_lot
        )
        product_lot_ml_without_package.write({"qty_done": 5.0, "lot_name": "A0002"})
        product_lot_second_pack = in_picking.put_in_pack()
        # Ensure packaging is set properly on pack
        product_lot_second_pack.product_packaging_id = (
            self.product_lot_cardbox_product_packaging
        )

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_lines.mapped("move_dest_ids.picking_id")
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_lines.mapped("location_dest_id"), self.stock_location
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
        self.warehouse.lot_stock_id.location_storage_type_ids = (
            self.cardboxes_location_storage_type
        )
        self.env["stock.storage.location.sequence"].create(
            {
                "package_storage_type_id": self.cardboxes_package_storage_type.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "sequence": 1,
            }
        )
        self.env["stock.storage.location.sequence"].create(
            {
                "package_storage_type_id": self.cardboxes_package_storage_type.id,
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
        self.cardboxes_location_storage_type.write({"do_not_mix_products": True})
        product = self.product
        packaging = self.product_cardbox_product_packaging
        dest_location = self.cardboxes_location
        package = self.env["stock.quant.package"].create(
            {"name": "TEST1", "product_packaging_id": packaging.id}
        )
        quant = self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "package_id": package.id,
                "location_id": self.input_location.id,
            }
        )

        location = StockLocation._get_pack_putaway_strategy(
            dest_location, quant, product
        )

        # No location with given product -> the first bin should be returned
        self.assertEqual(location, self.cardboxes_bin_1_location)

        # Set a quantity in cardbox bin 4 to trigger the priority on the
        # location that already contains the product
        self.env["stock.quant"]._update_available_quantity(
            product, self.cardboxes_bin_3_location, 10.0,
        )
        location = StockLocation._get_pack_putaway_strategy(
            dest_location, quant, product
        )
        self.assertEqual(location, self.cardboxes_bin_3_location)

        # Set less quantity on bin 4. Since it's the location with less quantity
        # that should have priority
        self.env["stock.quant"]._update_available_quantity(
            product, self.cardboxes_bin_4_location, 1.0,
        )
        location = StockLocation._get_pack_putaway_strategy(
            dest_location, quant, product
        )
        self.assertEqual(location, self.cardboxes_bin_4_location)
