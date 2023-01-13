# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetQuantity(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.location_src
        cls.product = cls.product_a
        cls.packaging = cls.product_a_packaging
        cls.packaging.qty = 5

    @classmethod
    def _setup_picking(cls, lot=None):
        if lot:
            cls._set_product_tracking_by_lot(cls.product)
        cls._add_stock_to_product(cls.product, cls.location, 10, lot=lot)
        return cls._create_picking(lines=[(cls.product, 10)])

    def test_set_quantity_barcode_not_found(self):
        # First, select a picking
        picking = self._setup_picking()
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        move_line = picking.move_line_ids
        # Then try to scan an invalid barcode
        response = self.service.dispatch(
            "set_quantity", params={"selected_line_id": move_line.id, "barcode": "NOPE"}
        )
        expected_message = {"message_type": "error", "body": "Barcode not found"}
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_product_prefill_qty_disabled(self):
        # First, select a picking
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        response = self.service.dispatch(
            "set_quantity",
            params={"selected_line_id": move_line.id, "barcode": self.product.barcode},
        )
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.product_uom_qty} units.",
        }
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_product_prefill_qty_enabled(self):
        # First, select a picking
        self._enable_no_prefill_qty()
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        self.assertEqual(move_line.qty_done, 1)
        # We can scan the same product 9 times, and the qty will increment by 1
        # each time.
        for expected_qty in range(2, 11):
            response = self.service.dispatch(
                "set_quantity",
                params={
                    "selected_line_id": move_line.id,
                    "barcode": self.product.barcode,
                },
            )
            data = {
                "move_line": self._data_for_move_line(move_line),
                "asking_confirmation": False,
            }
            self.assert_response(response, next_state="set_quantity", data=data)
            self.assertEqual(move_line.qty_done, expected_qty)
        # However, once qty_done == product_uom_qty, scanning the product will
        # return an error
        response = self.service.dispatch(
            "set_quantity",
            params={"selected_line_id": move_line.id, "barcode": self.product.barcode},
        )
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.product_uom_qty} units.",
        }
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_lot_prefill_qty_disabled(self):
        # First, select a picking
        lot = self._create_lot_for_product(self.product, "LOT_BARCODE")
        picking = self._setup_picking(lot=lot)
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": lot.name},
        )
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        response = self.service.dispatch(
            "set_quantity",
            params={"selected_line_id": move_line.id, "barcode": lot.name},
        )
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.product_uom_qty} units.",
        }
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_lot_prefill_qty_enabled(self):
        # First, select a picking
        self._enable_no_prefill_qty()
        lot = self._create_lot_for_product(self.product, "LOT_BARCODE")
        picking = self._setup_picking(lot=lot)
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": lot.name},
        )
        move_line = picking.move_line_ids
        self.assertEqual(move_line.qty_done, 1)
        # We can scan the same lot 9 times (until qty_done == product_uom_qty),
        # and the qty will increment by 1 each time.
        for expected_qty in range(2, 11):
            response = self.service.dispatch(
                "set_quantity",
                params={"selected_line_id": move_line.id, "barcode": lot.name},
            )
            data = {
                "move_line": self._data_for_move_line(move_line),
                "asking_confirmation": False,
            }
            self.assert_response(response, next_state="set_quantity", data=data)
            self.assertEqual(move_line.qty_done, expected_qty)
        # However, once qty_done == product_uom_qty, scanning the lot will
        # return an error
        response = self.service.dispatch(
            "set_quantity",
            params={"selected_line_id": move_line.id, "barcode": lot.name},
        )
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.product_uom_qty} units.",
        }
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_packaging(self):
        """Scan a packaging to process an existing line."""
        # First, select a picking
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.packaging.barcode},
        )
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.packaging.barcode,
            },
        )
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.product_uom_qty} units.",
        }
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_packaging_with_allow_move_create(self):
        """Scan a packaging to create and then process a line.

        With no_prefill_qty disabled.
        """
        location = self.location
        self._add_stock_to_product(self.product, location, 10)
        self._enable_create_move_line()
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": self.packaging.barcode},
        )
        domain = self.service._scan_product__select_move_line_domain(
            self.product, location
        )
        move_line = self.env["stock.move.line"].search(domain, limit=1)
        self.assertEqual(move_line.qty_done, self.packaging.qty)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        data = {"location": self._data_for_location(location)}
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_set_quantity_scan_packaging_with_allow_move_create_and_no_prefill_qty(
        self,
    ):
        """Scan a packaging to create and then process a line.

        With no_prefill_qty enabled.
        """
        location = self.location
        self._add_stock_to_product(self.product, location, 10)
        self._enable_create_move_line()
        self._enable_no_prefill_qty()
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": self.packaging.barcode},
        )
        domain = self.service._scan_product__select_move_line_domain(
            self.product, location
        )
        move_line = self.env["stock.move.line"].search(domain, limit=1)
        self.assertEqual(move_line.qty_done, self.packaging.qty)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.packaging.barcode,
            },
        )
        expected_message = self.msg_store.unable_to_pick_more(self.packaging.qty)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        data = {"location": self._data_for_location(location)}
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_set_quantity_scan_packaging(self):
        """Scan a packaging to process an existing line."""
        # First, select a picking
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.packaging.barcode},
        )
        self.assertEqual(move_line.qty_done, move_line.product_uom_qty)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.packaging.barcode,
            },
        )
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.product_uom_qty} units.",
        }
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_scan_packaging_with_allow_move_create(self):
        """Scan a packaging to create and then process a line.

        With no_prefill_qty disabled.
        """
        self._add_stock_to_product(self.product, self.location, 10)
        self._enable_create_move_line()
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.packaging.barcode},
        )
        domain = self.service._scan_product__select_move_line_domain(
            self.product, self.location
        )
        move_line = self.env["stock.move.line"].search(domain, limit=1)
        self.assertEqual(move_line.qty_done, self.packaging.qty)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        self.assert_response(
            response, next_state="select_location", message=expected_message, data={}
        )

    def test_set_quantity_scan_packaging_with_allow_move_create_and_no_prefill_qty(
        self,
    ):
        """Scan a packaging to create and then process a line.

        With no_prefill_qty enabled.
        """
        self._add_stock_to_product(self.product, self.location, 10)
        self._enable_create_move_line()
        self._enable_no_prefill_qty()
        response = self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.packaging.barcode},
        )
        domain = self.service._scan_product__select_move_line_domain(
            self.product, self.location
        )
        move_line = self.env["stock.move.line"].search(domain, limit=1)
        self.assertEqual(move_line.qty_done, self.packaging.qty)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.packaging.barcode,
            },
        )
        expected_message = self.msg_store.unable_to_pick_more(self.packaging.qty)
        data = {"move_line": self._data_for_move_line(move_line)}
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        self.assert_response(
            response, next_state="select_location", message=expected_message, data={}
        )

    def test_set_quantity_invalid_dest_location(self):
        picking = self._setup_picking()
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        move_line = picking.move_line_ids
        # Then try to scan wrong_location
        wrong_location = self.env.ref("stock.stock_location_14")
        response = self.service.dispatch(
            "set_quantity",
            params={"selected_line_id": move_line.id, "barcode": wrong_location.name},
        )
        expected_message = {"message_type": "error", "body": "You cannot place it here"}
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_menu_default_location(self):
        picking = self._setup_picking()
        self.menu.sudo().allow_alternative_destination = True
        location = self.location
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": self.product.barcode},
        )
        # Change the destination on the move_line
        move_line = picking.move_line_ids
        move_line.location_dest_id = self.env.ref("stock.stock_location_14")
        # Scanning a child of the menu, shopfloor should ask for a confirmation
        params = {
            "selected_line_id": move_line.id,
            "barcode": self.dispatch_location.name,
        }
        response = self.service.dispatch("set_quantity", params=params)
        expected_message = {
            "message_type": "warning",
            "body": (
                f"Confirm location change from {move_line.location_dest_id.name} "
                f"to {self.dispatch_location.name}?"
            ),
        }
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": True,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )
        # Now, calling the same endpoint with confirm=True should be ok
        params["confirmation"] = True
        response = self.service.dispatch("set_quantity", params=params)
        expected_message = self.service.msg_store.transfer_done_success(
            move_line.picking_id
        )
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_set_quantity_child_move_location(self):
        picking = self._setup_picking()
        location = self.location
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": self.product.barcode},
        )
        # Change the destination on the move_line
        move_line = picking.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.name,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_action_cancel(self):
        # First, select a picking
        picking = self._setup_picking()
        self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.location.id,
                "barcode": self.product.barcode,
            },
        )
        move_line = picking.move_line_ids
        move_line.qty_done = 10.0
        # Result here already tested in
        # `test_scan_product::TestScanProduct::test_scan_product_with_move_line`
        response = self.service.dispatch(
            "set_quantity__action_cancel", params={"selected_line_id": move_line.id}
        )
        data = {}
        self.assert_response(response, next_state="select_location", data=data)
        # Ensure the qty_done and user has been reset.
        self.assertFalse(move_line.picking_id.user_id)
        self.assertEqual(move_line.qty_done, 0.0)
