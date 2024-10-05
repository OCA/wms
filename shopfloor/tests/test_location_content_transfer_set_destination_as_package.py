# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_location_content_transfer_base import LocationContentTransferCommonCase


class LocationContentTransferSetDestinationAsPackage(LocationContentTransferCommonCase):
    """Tests for endpoint used from scan_destination_... with a package."""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.content_loc
        )
        cls._fill_stock_for_moves(picking2.move_lines, location=cls.content_loc)
        cls.pickings.action_assign()
        cls._simulate_pickings_selected(cls.pickings)
        cls.sub_shelf1 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Sub Shelf 1",
                    "barcode": "subshelf1",
                    "location_id": cls.shelf1.id,
                }
            )
        )
        cls.location_package = cls.env["stock.quant.package"].create({})
        cls.empty_package = cls.env["stock.quant.package"].create({})

    def assert_all_done(self, destination, package=None):
        self.assertRecordValues(self.pickings, [{"state": "done"}, {"state": "done"}])
        self.assertRecordValues(
            self.pickings.move_line_ids,
            [
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
            ],
        )
        self.assertRecordValues(
            destination.quant_ids,
            [
                {"package_id": package.id},
                {"package_id": package.id},
                {"package_id": package.id},
                {"package_id": package.id},
            ],
        )

    def test_set_destination_all_dest_package_ok(self):
        """Scan package destination."""
        self._update_qty_in_location(
            self.sub_shelf1, self.product_a, 1, package=self.location_package
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.content_loc.id,
                "barcode": self.location_package.name,
            },
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.location_content_transfer_complete(
                self.content_loc, self.sub_shelf1
            ),
        )
        self.assert_all_done(self.sub_shelf1, self.location_package)

    def test_set_destination_line_package_ok(self):
        """Scanned destination package valid, moves set to done."""
        self._update_qty_in_location(
            self.sub_shelf1, self.product_a, 1, package=self.location_package
        )
        original_picking = self.picking2
        move_line = original_picking.move_line_ids[0]
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.location_package.name,
            },
        )
        # Check the resulting data
        # We got a new picking as the original one had two moves (and we
        # validated only one)
        new_picking = move_line.picking_id
        self.assertTrue(new_picking != original_picking)
        self.assertEqual(move_line.move_id.state, "done")
        self.assertEqual(move_line.picking_id.state, "done")
        self.assertEqual(original_picking.state, "assigned")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.sub_shelf1
            ),
        )
        self.assertRecordValues(
            self.sub_shelf1.quant_ids,
            [
                {"package_id": self.location_package.id},
                {"package_id": self.location_package.id},
            ],
        )

    def test_set_destination_package_dest_package_ok(self):
        """Scanned destination package valid, moves set to done."""
        self._update_qty_in_location(
            self.sub_shelf1, self.product_a, 1, package=self.location_package
        )
        original_picking = self.picking1
        package_level = original_picking.package_level_ids[0]
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.location_package.name,
            },
        )
        # Check the data (the whole transfer has been validated here w/o backorder)
        self.assertFalse(original_picking.backorder_ids)
        self.assertEqual(original_picking.state, "done")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.sub_shelf1
            ),
        )
        for move in package_level.move_line_ids.mapped("move_id"):
            self.assertEqual(move.state, "done")

    def test_set_destination_all_empty_package(self):
        """Scan an empty package as destination on set destination all."""
        # First scan the empty destination package
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.content_loc.id,
                "barcode": self.empty_package.name,
            },
        )
        self.assert_response_scan_destination_all(
            response,
            self.pickings,
            message=self.service.msg_store.package_selected_is_empty(
                self.empty_package
            ),
            package=self.empty_package,
        )
        # Then scan the destination location passing the empty package
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.content_loc.id,
                "barcode": self.sub_shelf1.barcode,
                "package_id": self.empty_package.id,
            },
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.location_content_transfer_complete(
                self.content_loc, self.sub_shelf1
            ),
        )
        self.assert_all_done(self.sub_shelf1, self.empty_package)

    def test_set_destination_line_empty_package(self):
        """Scan an empty package as destination on set destination line."""
        original_picking = self.picking2
        move_line = original_picking.move_line_ids[0]
        # First scan the empty destination package
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.empty_package.name,
            },
        )
        self.assert_response_scan_destination(
            response,
            move_line,
            message=self.service.msg_store.package_selected_is_empty(
                self.empty_package
            ),
            package=self.empty_package,
        )
        # Then scan the destination location passing the empty package
        response = self.service.dispatch(
            "set_destination_line",
            params={
                "location_id": self.content_loc.id,
                "move_line_id": move_line.id,
                "quantity": move_line.product_uom_qty,
                "barcode": self.sub_shelf1.barcode,
                "package_id": self.empty_package.id,
            },
        )
        # Check the resulting data
        # We got a new picking as the original one had two moves (and we
        # validated only one)
        new_picking = move_line.picking_id
        self.assertTrue(new_picking != original_picking)
        self.assertEqual(move_line.move_id.state, "done")
        self.assertEqual(move_line.picking_id.state, "done")
        self.assertEqual(original_picking.state, "assigned")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.sub_shelf1
            ),
        )
        # Check the correct package has been assigned
        self.assertRecordValues(
            self.sub_shelf1.quant_ids,
            [
                {"package_id": self.empty_package.id},
            ],
        )

    def test_set_destination_package_dest_empty_package(self):
        """Scan an empty destination package on set destination package."""
        original_picking = self.picking1
        package_level = original_picking.package_level_ids[0]
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.empty_package.name,
            },
        )
        self.assert_response_scan_destination(
            response,
            package_level,
            message=self.service.msg_store.package_selected_is_empty(
                self.empty_package
            ),
            package=self.empty_package,
        )
        response = self.service.dispatch(
            "set_destination_package",
            params={
                "location_id": self.content_loc.id,
                "package_level_id": package_level.id,
                "barcode": self.sub_shelf1.barcode,
                "package_id": self.empty_package.id,
            },
        )
        # Check the data (the whole transfer has been validated here w/o backorder)
        self.assertFalse(original_picking.backorder_ids)
        self.assertEqual(original_picking.state, "done")
        # Check the response
        move_lines = self.service._find_transfer_move_lines(self.content_loc)
        self.assert_response_start_single(
            response,
            move_lines.mapped("picking_id"),
            message=self.service.msg_store.location_content_transfer_item_complete(
                self.sub_shelf1
            ),
        )
        for move in package_level.move_line_ids.mapped("move_id"):
            self.assertEqual(move.state, "done")
        # Check the correct package has been assigned
        self.assertRecordValues(
            self.sub_shelf1.quant_ids,
            [
                {"package_id": self.empty_package.id},
                {"package_id": self.empty_package.id},
            ],
        )
