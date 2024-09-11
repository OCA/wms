# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import const_eval

from .common import TestStorageTypeCommon


class TestStorageTypeMove(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.areas.write({"pack_putaway_strategy": "ordered_locations"})

    def assert_package_level_domain(self, json_domain, expected_locations):
        domain = const_eval(json_domain)
        self.assertEqual(len(domain), 1)
        self.assertEqual(domain[0][0], "id")
        self.assertEqual(domain[0][1], "in")
        self.assertEqual(sorted(domain[0][2]), sorted(expected_locations.ids))

    def _test_confirmed_move(self, product=None):
        confirmed_move = self._create_single_move(product or self.product)
        confirmed_move.location_dest_id = self.pallets_bin_1_location.id
        move_to_assign = self._create_single_move(self.product)
        (confirmed_move | move_to_assign)._assign_picking()
        package = self.env["stock.quant.package"].create(
            # {"product_packaging_id": self.product_pallet_product_packaging.id}
            {"package_type_id": self.pallet_pack_type.id}
        )
        self._update_qty_in_location(
            move_to_assign.location_id,
            move_to_assign.product_id,
            move_to_assign.product_qty,
            package=package,
        )
        move_to_assign._action_assign()
        return move_to_assign

    def test_not_only_empty_confirmed_move(self):
        self.pallets_location_storage_type.write({"allow_new_product": "mixed"})
        move = self._test_confirmed_move()
        self.assertEqual(
            move.move_line_ids.location_dest_id, self.pallets_bin_1_location
        )

    def test_only_empty_confirmed_move(self):
        self.pallets_location_storage_type.write({"allow_new_product": "empty"})
        move = self._test_confirmed_move()
        self.assertNotEqual(
            move.move_line_ids.location_dest_id, self.pallets_bin_1_location
        )

    def test_do_not_mix_products_confirmed_move_ok(self):
        self.pallets_location_storage_type.write({"allow_new_product": "same"})
        move = self._test_confirmed_move()
        self.assertEqual(
            move.move_line_ids.location_dest_id, self.pallets_bin_1_location
        )

    def test_do_not_mix_products_confirmed_move_nok(self):
        self.pallets_location_storage_type.write({"allow_new_product": "same"})
        move_other_product = self._test_confirmed_move(
            self.env.ref("product.product_product_10")
        )
        self.assertNotEqual(
            move_other_product.move_line_ids.location_dest_id,
            self.pallets_bin_1_location,
        )

    def test_package_level_location_dest_domain_only_empty(self):
        # Set pallets location type as only empty
        self.pallets_location_storage_type.write({"allow_new_product": "empty"})
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
        # Second move line goes into pallets bin 2
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_2_location,
        )
        self.assertEqual(
            int_picking.package_level_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location | self.pallets_bin_2_location,
        )
        package_type_locations = int_picking.package_level_ids.mapped(
            "package_id.package_type_id." "storage_location_sequence_ids.location_id"
        )
        possible_locations = self.env["stock.location"].search(
            [
                (
                    "computed_storage_category_id.capacity_ids",
                    "in",
                    int_picking.package_level_ids.mapped(
                        "package_id.package_type_id.storage_category_capacity_ids"
                    ).ids,
                ),
                ("location_id", "child_of", int_picking.location_dest_id.id),
                ("id", "in", package_type_locations.mapped("leaf_location_ids").ids),
            ]
        )
        only_empty_possible_locations = possible_locations.filtered(
            lambda l: not l.quant_ids
        )

        for level in int_picking.package_level_ids:
            self.assertEqual(
                level.allowed_location_dest_ids,
                only_empty_possible_locations
                - (
                    # remove the destination of other levels but keep the current one
                    int_picking.package_level_ids.mapped("location_dest_id")
                )
                | level.location_dest_id,
            )

        # Update qty in a bin to ensure it's not in possible locations anymore
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.pallets_bin_3_location, 1.0
        )
        only_empty_possible_locations_2 = possible_locations.filtered(
            lambda l: not l.quant_ids
        )
        self.assertEqual(
            only_empty_possible_locations,
            only_empty_possible_locations_2 | self.pallets_bin_3_location,
        )

        for level in int_picking.package_level_ids:
            self.assertEqual(
                level.allowed_location_dest_ids,
                only_empty_possible_locations_2
                - (
                    # remove the destination of other levels but keep the current one
                    int_picking.package_level_ids.mapped("location_dest_id")
                )
                | level.location_dest_id,
            )

        # Creating a new possible location must be reflected in domain
        pallets_bin_4_location = self.env["stock.location"].create(
            {"name": "Pallets bin 4", "location_id": self.pallets_location.id}
        )

        for level in int_picking.package_level_ids:
            self.assertEqual(
                level.allowed_location_dest_ids,
                (only_empty_possible_locations_2 | pallets_bin_4_location)
                - (
                    # remove the destination of other levels but keep the current one
                    int_picking.package_level_ids.mapped("location_dest_id")
                )
                | level.location_dest_id,
            )

    def test_package_level_location_dest_domain_mixed(self):
        # Mark picking to allow creation and use of existing lots in order
        # to register two times the same lot in different packages
        self.receipts_picking_type.use_existing_lots = True
        self.cardboxes_location_storage_type.write({"allow_new_product": "same_lot"})
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
                            "product_uom_qty": 52.0,
                            "product_uom": self.product.uom_id.id,
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
                            "product_uom_qty": 15.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    ),
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        ).qty_done = 48.0
        first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        # Put in pack again
        product_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product and not ml.result_package_id
        )
        product_ml_without_package.qty_done = 4.0
        second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_cardbox_product_packaging
        # Create lots to be used on move lines
        lot_a0001 = self.env["stock.lot"].create(
            {
                "name": "A0001",
                "product_id": self.product_lot.id,
                "company_id": self.env.user.company_id.id,
            }
        )
        lot_a0002 = self.env["stock.lot"].create(
            {
                "name": "A0002",
                "product_id": self.product_lot.id,
                "company_id": self.env.user.company_id.id,
            }
        )
        # Put in pack lot product
        in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_lot
        ).write({"qty_done": 5.0, "lot_id": lot_a0001.id})
        third_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        third_pack.product_packaging_id = self.product_lot_cardbox_product_packaging
        # Put in pack lot product again
        product_lot_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_lot and not ml.result_package_id
        )
        product_lot_ml_without_package.write({"qty_done": 5.0, "lot_id": lot_a0002.id})
        fourth_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        fourth_pack.product_packaging_id = self.product_lot_cardbox_product_packaging
        # Put in pack lot product again ... again (to have two times same lot)
        product_lot_ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_lot and not ml.result_package_id
        )
        product_lot_ml_without_package.write({"qty_done": 5.0, "lot_id": lot_a0002.id})
        fifth_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        fifth_pack.product_packaging_id = self.product_lot_cardbox_product_packaging
        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.move_dest_ids.picking_id
        int_picking.action_assign()

        def _get_possible_locations(package_level):
            storage_type = package_level.package_id.package_type_id
            package_type_locations = storage_type.storage_location_sequence_ids.mapped(
                "location_id.leaf_location_ids"
            )
            possible_locations = self.env["stock.location"].search(
                [
                    (
                        "computed_storage_category_id.capacity_ids",
                        "in",
                        storage_type.storage_category_capacity_ids.ids,
                    ),
                    (
                        "location_id",
                        "child_of",
                        package_level.picking_id.location_dest_id.id,
                    ),
                    ("id", "in", package_type_locations.ids),
                ]
            )
            return (
                possible_locations
                - package_level.picking_id.package_level_ids.mapped("location_dest_id")
                | pack_level.location_dest_id
            )

        def _levels_for(packages):
            return self.env["stock.package_level"].search(
                [
                    ("package_id", "in", packages.ids),
                    ("picking_id", "=", int_picking.id),
                ]
            )

        first_level = _levels_for(first_package)
        self.assertEqual(len(first_level), 1)
        # Pallet into pallets bin
        self.assertEqual(first_level.location_dest_id, self.pallets_bin_1_location)

        second_level = _levels_for(second_pack)
        # Cardbox into cardbox bin
        self.assertEqual(len(second_level), 1)
        self.assertEqual(second_level.location_dest_id, self.cardboxes_bin_1_location)

        third_level = _levels_for(third_pack)

        # Cardbox with different product go into different cardbox location
        self.assertEqual(len(third_level), 1)
        self.assertEqual(third_level.location_dest_id, self.cardboxes_bin_3_location)

        fourth_fifth_levels = _levels_for(fourth_pack | fifth_pack)
        # Cardbox with same product but different lot go into different
        # cardbox location
        # Cardbox with same product same lot go into same location
        self.assertEqual(len(fourth_fifth_levels), 2)
        self.assertEqual(
            fourth_fifth_levels.location_dest_id, self.cardboxes_bin_2_location
        )

        for pack_level in (
            first_level | second_level | third_level | fourth_fifth_levels
        ):
            # Check domain
            self.assertEqual(
                pack_level.allowed_location_dest_ids,
                _get_possible_locations(pack_level),
            )

            # Set the quantities done in order to avoid immediate transfer wizard
            for move_line in pack_level.move_line_ids:
                move_line.qty_done = move_line.reserved_qty

        second_level.location_dest_id = third_level.location_dest_id
        with self.assertRaises(ValidationError):
            int_picking.button_validate()

    def test_stock_move_no_package(self):
        """
        Create a stock move for a product with lot restriction
        Don't put it in a package
        Check that lot restriction is well applied
        """
        # Constrain Cardbox Capacity to accept same lots only
        self.cardboxes_location_storage_type.write({"allow_new_product": "same_lot"})
        # Set a quantity in cardbox bin 2 to make sure constraint is applied
        self.env["stock.quant"]._update_available_quantity(
            self.env.ref("product.product_product_10"),
            self.cardboxes_bin_2_location,
            1.0,
        )

        # As we don't put in pack in this flow, we need to set a default
        # package type on the product level in order to get the specialized putaway
        # to be applied
        self.product_lot.package_type_id = self.cardboxes_package_storage_type

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

        # Fill in the lots during the incoming process
        product_lot_ml = in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product_lot
        )
        product_lot_ml.write({"qty_done": 5.0, "lot_name": "A0001"})
        product_lot_ml.copy({"qty_done": 3.0, "lot_name": "A0002"})

        product_ml = in_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        )

        product_ml.write({"qty_done": 8.0})

        in_picking._action_done()

        int_picking = in_picking.move_ids.mapped("move_dest_ids.picking_id")

        lot_lines = int_picking.move_line_ids.filtered(
            lambda line: line.product_id == self.product_lot
        )
        destination_ids = lot_lines.mapped("location_dest_id.id")
        # Check if the destinations are all different
        self.assertEqual(
            len(set(destination_ids)),
            len(destination_ids),
        )

        lot_ids = lot_lines.mapped("lot_id.id")
        # Check if the lots are all different
        self.assertEqual(
            len(set(lot_ids)),
            len(lot_ids),
        )
