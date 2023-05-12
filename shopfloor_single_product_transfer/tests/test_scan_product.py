# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase

LOGGER_NAME = "shopfloor.services.single_product_transfer"
ROLLBACK_LOG = (
    "INFO:shopfloor.services.single_product_transfer:"
    "scan_product returned an error/warning. "
    "Transaction rollbacked."
)
NO_LOG_EXCEPTION = (
    "no logs of level INFO or higher triggered on "
    "shopfloor.services.single_product_transfer"
)


class TestScanProduct(CommonCase):
    @classmethod
    def _create_putaway_rule(cls, product, location_src, location_dest):
        putaway_model = cls.env["stock.putaway.rule"].sudo()
        cls.putaway_rule = putaway_model.create(
            {
                "product_id": product.id,
                "location_in_id": location_src.id,
                "location_out_id": location_dest.id,
            }
        )

    def test_scan_wrong_barcode(self):
        location = self.location_src
        response = self.service.dispatch(
            "scan_product", params={"location_id": location.id, "barcode": "NOPE"}
        )
        expected_message = {"message_type": "error", "body": "Barcode not found"}
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_tracked_product(self):
        location = self.location_src
        product = self.product_a
        self._set_product_tracking_by_lot(product)
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product",
                params={"location_id": location.id, "barcode": product.barcode},
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        expected_message = {
            "message_type": "warning",
            "body": "Product tracked by lot, please scan one.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_product_multiple_lines_in_picking_no_prefill_qty_enabled(self):
        self._enable_no_prefill_qty()
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        # Without argument, a multi line picking is created
        # with product_a and product_b
        picking = self._create_picking()
        move_line = picking.move_line_ids.filtered(lambda l: l.product_id == product)
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": product.barcode},
        )
        # a new picking should have been created for the selected move line
        new_picking = self.get_new_picking()
        self.assertTrue(new_picking)
        self.assertEqual(move_line.picking_id, new_picking)
        self.assertEqual(move_line.qty_done, 1)
        self.assertEqual(move_line.product_uom_qty, 10.0)

    def test_scan_product_no_move_line(self):
        # No move with product in location, create move line is disabled.
        # Scanning the product should return a `No operation found` error
        location = self.location_src
        product = self.product_a
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product",
                params={"location_id": location.id, "barcode": product.barcode},
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        expected_message = {
            "message_type": "error",
            "body": "No operation found for this menu and profile.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_product_with_move_line(self):
        # No move with product in location, create move line is disabled.
        # Scanning the product should return a `No operation found` error
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        picking = self._create_picking(lines=[(product, 10)])
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": product.barcode},
                )
        move_line = picking.move_line_ids
        self.assertTrue(move_line.picking_id.user_id)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_product_with_stock_create_move_disabled(self):
        # No move with product in location, create move line is enabled but
        # there's no stock.
        # Scanning the product should return a `No operation found` error
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product",
                params={"location_id": location.id, "barcode": product.barcode},
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        self.assertFalse(self.get_new_move_line())
        expected_message = {
            "message_type": "error",
            "body": "No operation found for this menu and profile.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_product_with_stock_create_move_enabled(self):
        # No move with product in location, create move line is enabled but
        # there's no stock.
        # Scanning the product should return a `No operation found` error
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        self._enable_create_move_line()
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": product.barcode},
                )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        self.assertTrue(move_line.picking_id.user_id)
        self.assertEqual(move_line.product_qty, 10.0)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_product_with_reserved_stock_unreserve_move_disabled(self):
        # No move with product in location, create move line is enabled but
        # there's no stock.
        # Scanning the product should return a `No operation found` error
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        self._enable_create_move_line()
        # This picking has reserved the only available goods
        self._create_picking(
            lines=[(product, 10)], picking_type=self.other_picking_type
        )
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product",
                params={"location_id": location.id, "barcode": product.barcode},
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        self.assertFalse(self.get_new_move_line())
        expected_message = {
            "message_type": "error",
            "body": "No operation found for this menu and profile.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_product_with_reserved_stock_unreserve_move_enabled(self):
        # No move with product in location, create move line is enabled but
        # there's no stock.
        # Scanning the product should return a `No operation found` error
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._enable_unreserve_other_moves()
        self._add_stock_to_product(product, location, 10)
        # This picking has reserved the only available goods
        self._create_picking(
            lines=[(product, 10)], picking_type=self.other_picking_type
        )
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": product.barcode},
                )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        self.assertTrue(move_line.picking_id.user_id)
        self.assertEqual(move_line.product_qty, 10.0)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_lot_no_move_line(self):
        location = self.location_src
        product = self.product_a
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product", params={"location_id": location.id, "barcode": lot.name}
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        expected_message = {
            "message_type": "error",
            "body": "No operation found for this menu and profile.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_lot_with_move_line(self):
        location = self.location_src
        product = self.product_a
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        self._add_stock_to_product(product, location, 10, lot=lot)
        picking = self._create_picking(lines=[(product, 10)])
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": lot.name},
                )
        move_line = picking.move_line_ids
        self.assertTrue(move_line.picking_id.user_id)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_lot_with_stock_create_move_disabled(self):
        location = self.location_src
        product = self.product_a
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        self._add_stock_to_product(product, location, 10, lot=lot)
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product", params={"location_id": location.id, "barcode": lot.name}
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        self.assertFalse(self.get_new_move_line())
        expected_message = {
            "message_type": "error",
            "body": "No operation found for this menu and profile.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_lot_with_stock_create_move_enabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        self._add_stock_to_product(product, location, 10, lot=lot)
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": lot.name},
                )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        self.assertTrue(move_line.picking_id.user_id)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_lot_with_reserved_stock_unreserve_move_disabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        self._add_stock_to_product(product, location, 10, lot=lot)
        # This picking has reserved the only available goods
        self._create_picking(
            lines=[(product, 10)], picking_type=self.other_picking_type
        )
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product", params={"location_id": location.id, "barcode": lot.name}
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        self.assertFalse(self.get_new_move_line())
        expected_message = {
            "message_type": "error",
            "body": "No operation found for this menu and profile.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_scan_lot_with_reserved_stock_unreserve_move_enabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._enable_unreserve_other_moves()
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        self._add_stock_to_product(product, location, 10, lot=lot)
        # This picking has reserved the only available goods
        self._create_picking(
            lines=[(product, 10)], picking_type=self.other_picking_type
        )
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": lot.name},
                )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        self.assertTrue(move_line.picking_id.user_id)
        self.assertEqual(move_line.product_qty, 10.0)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_product_no_putaway_ignore_no_putaway_enabled(self):
        # Ignore no putaway available is set, and no putaway rule is defined.
        # Returns an error message, and no move line has been created.
        self._enable_create_move_line()
        self._enable_ignore_no_putaway_available()
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        with self.assertLogs(LOGGER_NAME) as log_catcher:
            response = self.service.dispatch(
                "scan_product",
                params={"location_id": location.id, "barcode": product.barcode},
            )
            self.assertIn(ROLLBACK_LOG, log_catcher.output)
        self.assertFalse(self.get_new_move_line())
        expected_message = {
            "message_type": "error",
            "body": "No putaway destination is available.",
        }
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", data=data, message=expected_message
        )

    def test_scan_product_no_putaway_ignore_no_putaway_disabled(self):
        # Ignore no putaway available is not set, and no putaway rule is defined.
        # Creates a move line.
        self._enable_create_move_line()
        location = self.location_src
        product = self.product_a
        self._add_stock_to_product(product, location, 10)
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": product.barcode},
                )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_scan_product_with_putaway_ignore_no_putaway_enabled(self):
        # Ignore no putawai available is set, and a putaway is defined.
        # Creates a move line
        location = self.location_src
        product = self.product_a
        location_dest = self.location_dest
        location_putaway_dest = self.env.ref("stock.location_refrigerator_small")
        self._create_putaway_rule(product, location_dest, location_putaway_dest)
        self._enable_create_move_line()
        self._enable_ignore_no_putaway_available()
        self._add_stock_to_product(product, location, 10)
        with self.assertRaisesRegex(AssertionError, NO_LOG_EXCEPTION):
            with self.assertLogs(LOGGER_NAME):
                response = self.service.dispatch(
                    "scan_product",
                    params={"location_id": location.id, "barcode": product.barcode},
                )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)

    def test_create_move_line_by_product_no_prefill_qty_disabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        max_qty_done = 10
        self._add_stock_to_product(product, location, max_qty_done)
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": product.barcode},
        )
        move_line = self.get_new_move_line()
        self.assertEqual(move_line.qty_done, max_qty_done)
        self.assertEqual(move_line.product_uom_qty, max_qty_done)

    def test_create_move_line_by_product_no_prefill_qty_enabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._enable_no_prefill_qty()
        max_qty_done = 10
        self._add_stock_to_product(product, location, max_qty_done)
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": product.barcode},
        )
        move_line = self.get_new_move_line()
        self.assertEqual(move_line.qty_done, 1)
        self.assertEqual(move_line.product_uom_qty, max_qty_done)

    def test_create_move_line_by_lot_no_prefill_qty_disabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        max_qty_done = 10
        self._add_stock_to_product(product, location, max_qty_done, lot=lot)
        self.service.dispatch(
            "scan_product", params={"location_id": location.id, "barcode": lot.name}
        )
        move_line = self.get_new_move_line()
        self.assertEqual(move_line.qty_done, max_qty_done)
        self.assertEqual(move_line.product_uom_qty, max_qty_done)

    def test_create_move_line_by_lot_no_prefill_qty_enabled(self):
        location = self.location_src
        product = self.product_a
        self._enable_create_move_line()
        self._enable_no_prefill_qty()
        self._set_product_tracking_by_lot(product)
        lot = self._create_lot_for_product(product, "LOT_BARCODE")
        max_qty_done = 10
        self._add_stock_to_product(product, location, max_qty_done, lot=lot)
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": lot.name},
        )
        move_line = self.get_new_move_line()
        self.assertEqual(move_line.qty_done, 1)
        self.assertEqual(move_line.product_uom_qty, max_qty_done)

    def test_action_cancel(self):
        response = self.service.dispatch("scan_product__action_cancel")
        self.assert_response(response, next_state="select_location_or_package", data={})

    def test_scan_product_packaging(self):
        location = self.location_src
        packaging = self.product_a_packaging
        product = packaging.product_id
        self._add_stock_to_product(product, location, 10)
        picking = self._create_picking(lines=[(product, 10)])
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": packaging.barcode},
        )
        move_line = picking.move_line_ids
        self.assertTrue(move_line.picking_id.user_id)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
