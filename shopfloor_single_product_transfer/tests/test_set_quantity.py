# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetQuantity(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env.ref("stock.stock_location_components")
        cls.product = cls.product_a
        cls.packaging = cls.product_a_packaging
        cls.packaging.qty = 5

    @classmethod
    def _setup_picking(cls, lot=None):
        if lot:
            cls._set_product_tracking_by_lot(cls.product)
        cls._add_stock_to_product(cls.product, cls.location, 10, lot=lot)
        return cls._create_picking(lines=[(cls.product, 10)])

    @classmethod
    def _setup_chained_picking(cls, picking):
        next_moves = picking.move_ids.browse()
        for move in picking.move_ids:
            next_moves |= move.copy(
                {
                    "move_orig_ids": [(6, 0, move.ids)],
                    "location_id": move.location_dest_id.id,
                    "location_dest_id": cls.customer_location.id,
                }
            )
        next_moves._assign_picking()
        next_picking = next_moves.picking_id
        next_picking.action_confirm()
        next_picking.action_assign()
        return next_picking

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
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.quantity,
                "barcode": "NOPE",
            },
        )
        expected_message = {"message_type": "error", "body": "Barcode not found"}
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_quantity_line_done(self):
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        # We process the line correctly, which will mark the line as "done".
        self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.quantity,
                "barcode": self.dispatch_location.name,
            },
        )
        self.assertEqual(move_line.state, "done")
        # If we try to do it again, we're not allowed
        # and we're notified that the move is alread done.
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.quantity,
                "barcode": self.product.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        expected_message = self.msg_store.move_already_done()
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
        # Without no_prefill_qty, once selected, a moveline qty done is already
        # equal to the qty todo.
        self.assertTrue(move_line.picked)
        self.assertEqual(move_line.quantity, 10)
        self.assertEqual(move_line.qty_picked, 10)
        # We do not prevent the user to set a bigger qty
        # No qty check when scanning a product
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.product.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        # However, we prevent the user to post the line if qty_picked > quantity
        # quantity is checked when scanning a location
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.quantity} units.",
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
        self.assertEqual(move_line.qty_picked, 1)
        # We can scan the same product 9 times, and the qty will increment by 1
        # each time.
        for expected_qty in range(2, 11):
            response = self.service.dispatch(
                "set_quantity",
                params={
                    "selected_line_id": move_line.id,
                    "quantity": move_line.qty_picked,
                    "barcode": self.product.barcode,
                },
            )
            data = {
                "move_line": self._data_for_move_line(move_line),
                "asking_confirmation": None,
            }
            self.assert_response(response, next_state="set_quantity", data=data)
            self.assertEqual(move_line.qty_picked, expected_qty)
        # We do not prevent the user to set a qty_picked > quantity in the picker
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.product.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        # However, we prevent the user to post the line if qty_picked > quantity
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        expected_message = {
            "message_type": "error",
            "body": f"You must not pick more than {move_line.quantity} units.",
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )

    def test_set_picker_quantity(self):
        self._enable_no_prefill_qty()
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        self.assertEqual(move_line.qty_picked, 1)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 5.0,
                "barcode": self.product.barcode,
            },
        )
        # Here, user manually set 5.0 as qty done and scanned a product,
        # expected qty_picked on move line is 6.0
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        self.assertEqual(move_line.qty_picked, 6.0)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 10.0,
                "barcode": self.product.barcode,
            },
        )
        # Here user sets 10.0 then scans a product.
        # Expected qty_picked is 11.0
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        self.assertEqual(move_line.qty_picked, 11.0)
        # When scanning a location, a qty_picked is checked.
        # Since qty done > qty todo, an error should be raised

    def test_set_quantity_scan_lot_prefill_qty_disabled(self):
        # First, select a picking
        lot = self._create_lot_for_product(self.product, "LOT_BARCODE")
        picking = self._setup_picking(lot=lot)
        move_line = picking.move_line_ids
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": lot.name},
        )
        self.assertEqual(move_line.qty_picked, move_line.quantity)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": lot.name,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        # However, we shouldn't be able to confirm (scan a location)
        # since qty_picked > quantity (max is 10.0)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        expected_message = self.msg_store.unable_to_pick_more(10.0)
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
        self.assertEqual(move_line.qty_picked, 1)
        # We can scan the same lot 9 times (until qty_picked == quantity),
        # and the qty will increment by 1 each time.
        for expected_qty in range(2, 11):
            response = self.service.dispatch(
                "set_quantity",
                params={
                    "selected_line_id": move_line.id,
                    "quantity": move_line.qty_picked,
                    "barcode": lot.name,
                },
            )
            data = {
                "move_line": self._data_for_move_line(move_line),
                "asking_confirmation": None,
            }
            self.assert_response(response, next_state="set_quantity", data=data)
            self.assertEqual(move_line.qty_picked, expected_qty)
        # Nothing prevents the user to set qty_picked > quantity
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": lot.name,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        # However, we shouldn't be able to confirm (scan a location)
        # since qty_picked > quantity (max is 10.0)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        expected_message = self.msg_store.unable_to_pick_more(10.0)
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
        self.assertEqual(move_line.qty_picked, move_line.quantity)
        # picker qty is 10 + scanned packaging qty is 5 = 15
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.quantity,
                "barcode": self.packaging.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        self.assertEqual(move_line.qty_picked, 15.0)
        # However, we shouldn't be able to confirm (scan a location)
        # since quantity_picked > quantity (max is 10.0)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        expected_message = self.msg_store.unable_to_pick_more(10.0)
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
        self.assertTrue(move_line.quantity)
        self.assertEqual(move_line.quantity, 10.0)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.dispatch_location.barcode,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        data = {
            "location": self._data_for_location(location),
        }
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )
        self.assertEqual(move_line.location_dest_id, self.dispatch_location)
        self.assertEqual(move_line.location_id, location)
        self.assertEqual(
            move_line.move_id.location_dest_id,
            self.picking_type.default_location_dest_id,
        )
        self.assertEqual(move_line.move_id.location_id, location)

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
        self.assertEqual(move_line.qty_picked, 5.0)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.packaging.barcode,
            },
        )
        self.assertEqual(move_line.qty_picked, 10.0)
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        self.assert_response(response, next_state="set_quantity", data=data)
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": self.dispatch_location.barcode,
            },
        )
        expected_message = self.msg_store.unable_to_pick_more(self.packaging.qty)
        data = {"location": self._data_for_location(location)}
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_set_quantity_invalid_dest_location(self):
        picking = self._setup_picking()
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product.barcode},
        )
        move_line = picking.move_line_ids
        # Then try to scan wrong_location
        wrong_location = self.customer_location
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_picked,
                "barcode": wrong_location.barcode,
            },
        )
        expected_message = {"message_type": "error", "body": "You cannot place it here"}
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
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
            "quantity": move_line.qty_picked,
            "barcode": self.dispatch_location.barcode,
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
            "asking_confirmation": self.dispatch_location.barcode,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )
        # Now, calling the same endpoint with the confirmation set is ok
        params["confirmation"] = self.dispatch_location.barcode
        response = self.service.dispatch("set_quantity", params=params)
        expected_message = self.service.msg_store.transfer_done_success(
            move_line.picking_id
        )
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_set_quantity_confirm_with_different_barcode(self):
        picking = self._setup_picking()
        self.menu.sudo().allow_alternative_destination = True
        # Change the destination on the move_line
        move_line = picking.move_line_ids
        move_line.location_dest_id = self.env.ref("stock.stock_location_14")
        params = {
            "selected_line_id": move_line.id,
            "quantity": move_line.qty_picked,
            "barcode": self.dispatch_location.barcode,
        }
        # Setting the confirmation to another location barcode
        params["confirmation"] = self.dispatch_location.barcode + "DIFF"
        response = self.service.dispatch("set_quantity", params=params)
        # Confirmation is asked again for new location scanned
        message = self.service.msg_store.confirm_location_changed(
            move_line.location_dest_id, self.dispatch_location
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": self.dispatch_location.barcode,
        }
        self.assert_response(
            response, next_state="set_quantity", message=message, data=data
        )
        # Confirming the location with the same location
        params["confirmation"] = self.dispatch_location.barcode
        response = self.service.dispatch("set_quantity", params=params)
        expected_message = self.service.msg_store.transfer_done_success(
            move_line.picking_id
        )
        data = {"location": self._data_for_location(self.location)}
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
                "quantity": move_line.qty_picked,
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
        move_line._pick_qty(10.0)
        # Result here already tested in
        # `test_scan_product::TestScanProduct::test_scan_product_with_move_line`
        response = self.service.dispatch(
            "set_quantity__action_cancel", params={"selected_line_id": move_line.id}
        )
        data = {}
        self.assert_response(
            response, next_state="select_location_or_package", data=data
        )
        # Ensure qty_picked and user has been reset.
        self.assertFalse(move_line.picking_id.user_id)
        self.assertEqual(move_line.qty_picked, 0.0)
        # Ensure the picking is not cancelled if allow_move_create is not enabled
        self.assertTrue(move_line.picking_id.state == "assigned")

    def test_action_cancel_allow_move_create(self):
        # We perform the same actions as in test_action_cancel,
        # but with the allow_move_create option enabled
        self.menu.sudo().allow_move_create = True
        picking = self._setup_picking()
        self.service.dispatch(
            "scan_product",
            params={
                "location_id": self.location.id,
                "barcode": self.product.barcode,
            },
        )
        move_line = picking.move_line_ids
        move_line._pick_qty(10.0)
        response = self.service.dispatch(
            "set_quantity__action_cancel", params={"selected_line_id": move_line.id}
        )
        data = {}
        self.assert_response(
            response, next_state="select_location_or_package", data=data
        )
        # Ensure the picking is cancelled if allow_move_create is enabled
        self.assertFalse(move_line.exists())
        self.assertTrue(picking.state == "cancel")

    def test_set_quantity_done_with_completion_info(self):
        self.picking_type.sudo().display_completion_info = "next_picking_ready"
        picking = self._setup_picking()
        self._setup_chained_picking(picking)
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
                "quantity": move_line.qty_picked,
                "barcode": self.dispatch_location.name,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        completion_info = self.service._actions_for("completion.info")
        expected_popup = completion_info.popup(move_line)
        data = {"location": self._data_for_location(location)}
        self.assert_response(
            response,
            next_state="select_product",
            message=expected_message,
            data=data,
            popup=expected_popup,
        )

    def test_set_quantity_scan_location(self):
        self.menu.sudo().allow_move_create = False
        picking = self._setup_picking()
        self._setup_chained_picking(picking)
        location = self.location
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": self.product.barcode},
        )
        # Change the destination on the move_line and take less than the total
        # amount required.
        move_line = picking.move_line_ids
        self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 6,
                "barcode": self.dispatch_location.name,
            },
        )
        # If allow_move_create is disabled, a backorder is created.
        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", picking.id)]
        )
        self.assertEqual(
            backorder.move_line_ids.product_id, picking.move_line_ids.product_id
        )
        self.assertEqual(backorder.move_line_ids.qty_picked, 6.0)
        self.assertEqual(backorder.move_line_ids.state, "done")
        self.assertEqual(backorder.user_id, self.env.user)
        self.assertEqual(backorder.move_line_ids.shopfloor_user_id, self.env.user)
        self.assertEqual(picking.move_line_ids.quantity, 4.0)
        self.assertEqual(picking.move_line_ids.qty_picked, 0.0)
        self.assertEqual(picking.move_line_ids.state, "assigned")
        self.assertFalse(picking.move_line_ids.result_package_id)
        self.assertEqual(picking.user_id.id, False)
        self.assertEqual(picking.move_line_ids.shopfloor_user_id.id, False)
        self.assertEqual(picking.move_line_ids.location_dest_id, self.dispatch_location)
        self.assertEqual(picking.move_line_ids.location_id, self.location)
        self.assertEqual(
            picking.move_line_ids.move_id.location_dest_id,
            self.picking_type.default_location_dest_id,
        )
        self.assertEqual(
            picking.move_line_ids.move_id.location_id,
            self.picking_type.default_location_src_id,
        )

    def test_set_quantity_scan_location_allow_move_create(self):
        self.menu.sudo().allow_move_create = True
        picking = self._setup_picking()
        self._setup_chained_picking(picking)
        location = self.location
        self.service.dispatch(
            "scan_product",
            params={"location_id": location.id, "barcode": self.product.barcode},
        )
        # Change the destination on the move_line and take less than the total
        # amount required.
        move_line = picking.move_line_ids

        self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 6,
                "barcode": self.dispatch_location.name,
            },
        )
        # If allow_move_create is enabled, a backorder is not created
        # and the picking is marked as done with the scanned qty.
        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", picking.id)]
        )
        self.assertFalse(backorder)
        self.assertEqual(picking.move_line_ids.qty_picked, 6.0)
        self.assertEqual(picking.move_line_ids.state, "done")
        self.assertEqual(picking.move_line_ids.location_dest_id, self.dispatch_location)
        self.assertEqual(picking.move_line_ids.location_id, self.location)
        self.assertEqual(
            picking.move_line_ids.move_id.location_dest_id,
            self.picking_type.default_location_dest_id,
        )
        self.assertEqual(
            picking.move_line_ids.move_id.location_id,
            self.picking_type.default_location_src_id,
        )

    def test_set_quantity_scan_package_not_empty(self):
        # We scan a package that's not empty
        # and its location is selected.
        package = self._create_empty_package()
        self.env["stock.quant"].sudo().create(
            {
                "package_id": package.id,
                "location_id": self.dispatch_location.id,
                "product_id": self.product.id,
                "quantity": 10.0,
            }
        )
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 10.0,
                "barcode": package.name,
            },
        )
        expected_data = {
            "location": self._data_for_location(self.location),
        }
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        completion_info = self.service._actions_for("completion.info")
        expected_popup = completion_info.popup(move_line)
        self.assert_response(
            response,
            next_state="select_product",
            data=expected_data,
            message=expected_message,
            popup=expected_popup,
        )
        # We moved 10 units to an existing package
        self.assertEqual(package.quant_ids.quantity, 20.0)
        self.assertEqual(package, move_line.result_package_id)

    def test_set_quantity_scan_package_empty(self):
        # We scan an empty package
        # and are redirected to set_location.
        package = self._create_empty_package()
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 10.0,
                "barcode": package.name,
            },
        )
        expected_data = {
            "move_line": self._data_for_move_line(move_line),
            "package": self._data_for_package(package),
        }
        self.assert_response(
            response,
            next_state="set_location",
            data=expected_data,
        )
        self.assertEqual(package, move_line.result_package_id)

    def test_return_lot_from_customer(self):
        product = self.product
        self._set_product_tracking_by_lot(product)
        self._enable_create_move_line()
        quant_model = self.env["stock.quant"]
        # Set picking type locations for returns
        customer_location = self.customer_location
        stock_location = self.stock_location
        self.picking_type.sudo().write(
            {
                "default_location_src_id": customer_location.id,
                "default_location_dest_id": stock_location.id,
            }
        )
        # A lot has been shipped to customer, in a pack
        lot = self._create_lot_for_product(product, "LOTABCD")
        package = self._create_empty_package(name="PACKABCD")
        self._add_stock_to_product(
            product, customer_location, 1, lot=lot, package=package
        )
        qty_customer = quant_model._get_available_quantity(
            product, customer_location, lot_id=lot, package_id=package
        )
        self.assertEqual(qty_customer, 1)
        # Now try to return it in stock, scan the product, and ensure it creates a
        # new move line
        self.service.dispatch(
            "scan_product",
            params={"location_id": customer_location.id, "barcode": lot.name},
        )
        move_line = self.get_new_move_line()
        self.assertTrue(move_line)
        self.assertEqual(move_line.lot_id, lot)
        self.assertEqual(move_line.qty_picked, 1)
        self.assertEqual(move_line.move_id.picking_type_id, self.picking_type)
        # Move qty to stock
        self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": 1,
                "barcode": stock_location.barcode,
            },
        )
        qty_customer = quant_model._get_available_quantity(
            product, customer_location, lot_id=lot
        )
        self.assertEqual(qty_customer, 0)
        qty_stock = quant_model._get_available_quantity(
            product, stock_location, lot_id=lot
        )
        self.assertEqual(qty_stock, 1)
