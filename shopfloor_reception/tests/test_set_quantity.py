# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetQuantity(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a_packaging.qty = 5.0
        cls.packing_location.sudo().active = True
        package_model = cls.env["stock.quant.package"]
        cls.package_without_location = package_model.create(
            {
                "name": "PKG_WO_LOCATION",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls.package_with_location = package_model.create(
            {
                "name": "PKG_W_LOCATION",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls.package_with_location_child_of_dest = package_model.create(
            {
                "name": "PKG_W_LOCATION_CHILD",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls._update_qty_in_location(
            cls.packing_location, cls.product_a, 10, package=cls.package_with_location
        )
        cls._update_qty_in_location(
            cls.dispatch_location,
            cls.product_a,
            10,
            package=cls.package_with_location_child_of_dest,
        )

    def test_set_quantity_scan_product(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 10.0,
                "barcode": selected_move_line.product_id.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 11.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    def test_set_quantity_scan_packaging(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 10.0,
                "barcode": selected_move_line.product_id.packaging_ids.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 15.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    def test_scan_product(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 1.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )
        # Scan again, and ensure qty increments
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 4.0)

    def test_scan_packaging(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 5.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )
        # Scan again, and ensure qty increments
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 10.0)

    def test_scan_package_with_destination_child_of_dest_location(self):
        # next step is select_move
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.package_with_location_child_of_dest.name,
            },
        )
        self.assertEqual(
            selected_move_line.result_package_id,
            self.package_with_location_child_of_dest,
        )
        self.assertEqual(selected_move_line.location_dest_id, self.dispatch_location)
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )

    def test_scan_package_with_destination_not_child_of_dest_location(self):
        # next step is set_quantity with error
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.package_with_location.name,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_scan_package_without_location(self):
        # next_step is set_destination
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.package_without_location.name,
            },
        )
        self.assertEqual(
            selected_move_line.result_package_id, self.package_without_location
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_location_child_of_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.dispatch_location)
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )

    def test_scan_location_not_child_of_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.packing_location.barcode,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_scan_location_view_usage(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        self.dispatch_location.sudo().quant_ids.unlink()
        self.dispatch_location.sudo().usage = "view"
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_scan_new_package(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FooBar",
            },
        )
        picking_data = self.data.picking(picking)
        self.assertFalse(selected_move_line.result_package_id)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": picking_data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": "FooBar",
            },
            message={
                "message_type": "warning",
                "body": "Create new PACK FooBar? Scan it again to confirm.",
            },
        )
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FooBar",
                "confirmation": "FooBar",
            },
        )
        self.assertEqual(selected_move_line.result_package_id.name, "FooBar")
        picking_data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": picking_data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_reception_set_quantity_confirm_new_package_with_other_new_pack(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        # Scan new pack 1
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "Pack1",
            },
        )
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": self.data.move_lines(selected_move_line),
            "confirmation_required": "Pack1",
        }
        # System ask for confimation for Pack 1
        self.assert_response(
            response,
            next_state="set_quantity",
            data=data,
            message=self.msg_store.create_new_pack_ask_confirmation("Pack1"),
        )
        # Scan new pack 2
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "Pack2",
                "confirmation": "Pack1",
            },
        )
        # System ask for confimation for Pack 2
        data["confirmation_required"] = "Pack2"
        self.assert_response(
            response,
            next_state="set_quantity",
            data=data,
            message=self.msg_store.create_new_pack_ask_confirmation("Pack2"),
        )

    @classmethod
    def _shopfloor_manager_values(cls):
        vals = super()._shopfloor_manager_values()
        vals["groups_id"] = [(6, 0, [cls.env.ref("stock.group_stock_user").id])]
        return vals

    def _get_service_for_user(self, user):
        user_env = self.env(user=user)
        return self.get_service(
            "reception", menu=self.menu, profile=self.profile, env=user_env
        )

    def test_concurrent_update(self):
        # We're testing that move line's product uom qties are updated correctly
        # when users are workng on the same move in parallel
        picking = self._create_picking()
        self.service.dispatch("scan_document", params={"barcode": picking.name})
        self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assertEqual(len(selected_move_line), 1)
        self.assertEqual(selected_move_line.qty_done, 1.0)
        self.assertEqual(
            selected_move_line.product_uom_qty,
            selected_move_line.move_id.product_uom_qty,
        )

        # Let's make the first user work a little bit, and pick a total of 4 units
        for __ in range(4):
            self.service.dispatch(
                "set_quantity",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "quantity": selected_move_line.qty_done,
                    "barcode": selected_move_line.product_id.barcode,
                },
            )
        self.assertEqual(selected_move_line.qty_done, 5.0)
        self.assertEqual(selected_move_line.product_uom_qty, 10.0)

        # Now, concurrently pick products with another user for the same move
        manager_user = self.shopfloor_manager
        new_service = self._get_service_for_user(manager_user)
        new_service.dispatch("scan_document", params={"barcode": picking.name})
        new_service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        # The whole move's product_uom_qty has been assigned to the first created line.
        # The new one gets 0.0
        new_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
            and l.shopfloor_user_id == manager_user
        )
        self.assertEqual(new_line.product_uom_qty, 0.0)

        move_lines = selected_move_line | new_line
        line_service_mapping = [
            (selected_move_line, self.service),
            (new_line, new_service),
        ]

        # Now, we picked 5 for the original line, then 1 for the new one.
        # Total qty done should be 6
        lines_qty_done = sum(move_lines.mapped("qty_done"))
        self.assertEqual(lines_qty_done, 6.0)
        # should be equal to the moves quantity_done
        self.assertEqual(lines_qty_done, move_lines.move_id.quantity_done)

        # Now, let the new user finish its work
        for __ in range(4):
            new_service.dispatch(
                "set_quantity",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": new_line.id,
                    "quantity": new_line.qty_done,
                    "barcode": new_line.product_id.barcode,
                },
            )

        # We should have a qty_done == 10.0 on both moves and move lines
        lines_qty_done = sum(move_lines.mapped("qty_done"))
        self.assertEqual(lines_qty_done, 10.0)
        self.assertEqual(lines_qty_done, move_lines.move_id.quantity_done)

        # However, product_uom_qty hasn't changed
        self.assertEqual(selected_move_line.product_uom_qty, 10.0)
        self.assertEqual(new_line.product_uom_qty, 0.0)
        # And what's important is that the sum of lines's product_uom_qty is
        # always == move's product_uom_qty
        self.assertEqual(sum(move_lines.mapped("product_uom_qty")), 10.0)

        # However, if we pick more than move's product_uom_qty, then lines
        # product_uom_qty isn't updated, in order to be able to display an error
        # in the frontend

        for __ in range(2):
            new_service.dispatch(
                "set_quantity",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": new_line.id,
                    "quantity": new_line.qty_done,
                    "barcode": new_line.product_id.barcode,
                },
            )

        # We're 2 over move's product_uom_qty
        lines_qty_done = sum(move_lines.mapped("qty_done"))
        self.assertEqual(lines_qty_done, 12.0)
        self.assertEqual(lines_qty_done, move_lines.move_id.quantity_done)

        # We shouldn't be able to process any of those move lines
        error_msg = {
            "message_type": "error",
            "body": "You cannot process that much units.",
        }
        picking_data = self.data.picking(picking)
        quantity_done_by_user = 1
        for line, service in line_service_mapping:
            quantity_done_by_user += 2
            response = service.dispatch(
                "process_with_new_pack",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": line.id,
                    "quantity": line.qty_done,
                },
            )
            line_data = self.data.move_lines(line)
            line_data[0]["quantity"] = quantity_done_by_user
            self.assert_response(
                response,
                next_state="set_quantity",
                data={
                    "picking": picking_data,
                    "confirmation_required": None,
                    "selected_move_line": line_data,
                },
                message=error_msg,
            )

        # But line's product_uom_qty hasn't changed and is still 10.0
        self.assertEqual(sum(move_lines.mapped("product_uom_qty")), 10.0)

        # If we lower by 2 the first move qty done, qty_todo will be updated correctly
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 2.0,
                "barcode": selected_move_line.product_id.barcode,
            },
        )

        self.assertEqual(selected_move_line.qty_done, 3.0)
        self.assertEqual(new_line.qty_done, 7.0)

        self.assertEqual(selected_move_line.product_uom_qty, 10.0)
        self.assertEqual(new_line.product_uom_qty, 0.0)
        self.assertEqual(sum(move_lines.mapped("product_uom_qty")), 10.0)

        # And everything's fine on the move
        move = move_lines.move_id
        self.assertEqual(move.product_uom_qty, move.quantity_done)
        self.assertEqual(move.product_uom_qty, 10.0)

    def test_split_move_line(self):
        picking = self._create_picking()
        self.service.dispatch("scan_document", params={"barcode": picking.name})
        self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assertEqual(len(selected_move_line), 1)
        self.assertEqual(selected_move_line.qty_done, 1.0)
        # Now, concurrently pick products with another user for the same move
        manager_user = self.shopfloor_manager
        new_service = self._get_service_for_user(manager_user)
        new_service.dispatch("scan_document", params={"barcode": picking.name})
        new_service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )

        # Try to process the first line
        response = self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 1.0,
            },
        )
        picking_data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": picking_data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )
        # there should be 3 lines now
        move_lines = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assertEqual(len(move_lines), 3)

    def test_concurrent_update_2(self):
        self.menu.sudo().auto_post_line = True
        self.input_location.sudo().active = True
        # Test related to picking being set to "ready" once the first user posts
        # its move line, hence the picking being not available in shopfloor afterwards.

        # The reason for that is that `_post_line` calls `_recompute_state`.
        # If at this point there's more or less reserved qty than what's been ordered
        # then state isn't computed as assigned.

        # This test ensure that this isn't the case anymore.

        # Creating the picking, selecting the move line.
        picking = self._create_picking()
        move = picking.move_lines.filtered(lambda l: l.product_id == self.product_a)
        service_user_1 = self.service
        service_user_1.dispatch("scan_document", params={"barcode": picking.name})
        service_user_1.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        move_line_user_1 = move.move_line_ids
        # The only move line should have qty_done = 1
        self.assertEqual(move_line_user_1.qty_done, 1.0)
        self.assertEqual(move_line_user_1.product_uom_qty, 10.0)

        # Now, concurrently pick products with another user for the same move
        manager_user = self.shopfloor_manager
        service_user_2 = self._get_service_for_user(manager_user)
        service_user_2.dispatch("scan_document", params={"barcode": picking.name})
        service_user_2.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        # The whole move's product_uom_qty has been assigned to the first created line.
        # The new one gets 0.0
        move_line_user_2 = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
            and l.shopfloor_user_id == manager_user
        )
        self.assertEqual(move_line_user_2.product_uom_qty, 0.0)
        self.assertEqual(move_line_user_2.qty_done, 1.0)

        # At this point, both lines are referencing the same move
        self.assertEqual(move_line_user_2.move_id, move_line_user_1.move_id)

        # A new move / picking will be created after it is posted.
        # store the list of pickings to find it out after it is posted
        # moves before
        lines_before = self.env["stock.move.line"].search([])

        # Now, post user_1 move line
        response = service_user_1.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
                "quantity": move_line_user_1.qty_done,
            },
        )
        picking_data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": picking_data,
                "selected_move_line": self.data.move_lines(move_line_user_1),
            },
        )

        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
                "location_name": self.input_location.name,
            },
        )
        lines_after = self.env["stock.move.line"].search(
            [("id", "not in", lines_before.ids)]
        )
        # After move_line is posted, its state is done, and its qty_done is 1.0
        self.assertEqual(move_line_user_1.state, "done")
        # The remaining one is still to be done
        self.assertEqual(move_line_user_2.state, "assigned")
        # As well as the new one
        self.assertEqual(len(lines_after), 1)
        # The quantity to do is set on 1 of the lines
        self.assertEqual(lines_after.product_uom_qty, 0)
        self.assertEqual(move_line_user_2.product_uom_qty, 9)

    def test_move_states(self):
        # as only assigned moves can be posted, we need to ensure that
        # we got the right states in any case, especially when users are working
        # concurrently
        picking = self._create_picking()
        move_product_a = picking.move_lines.filtered(
            lambda l: l.product_id == self.product_a
        )
        # user1 processes 10 units
        move_line_user_1 = move_product_a.move_line_ids
        service_user_1 = self.service
        service_user_1.dispatch("scan_document", params={"barcode": picking.name})
        service_user_1.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        response = service_user_1.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
                "quantity": move_product_a.product_qty - 1,
                "barcode": self.product_a.barcode,
            },
        )
        # user2 selects the same picking
        user2 = self.shopfloor_manager
        service_user_2 = self._get_service_for_user(user2)
        response = service_user_2.dispatch(
            "scan_document", params={"barcode": picking.name}
        )
        # And the same line
        service_user_2.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        move_line_user_2 = move_product_a.move_line_ids - move_line_user_1
        # user1 shouldn't be able to process his move, since
        # move qty_done  > move product_qty
        response = service_user_1.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
                "quantity": 10.0,
            },
        )
        #
        expected_message = {
            "body": "You cannot process that much units.",
            "message_type": "error",
        }
        self.assertMessage(response, expected_message)
        # user1 cancels the operation
        service_user_1.dispatch(
            "set_quantity__cancel_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
            },
        )
        self.assertFalse(move_line_user_1.shopfloor_user_id)
        self.assertEqual(move_line_user_1.qty_done, 0)
        # User2 should be able to process 1 unit
        response = service_user_2.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_2.id,
                "quantity": 1.0,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(move_line_user_2),
            },
        )
        self.assertEqual(move_product_a.quantity_done, 1.0)
        response = service_user_2.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_2.id,
                "location_name": self.dispatch_location.name,
            },
        )
        # When posted, the move line product_uom_qty has been set to qty_done
        self.assertEqual(move_line_user_2.qty_done, move_line_user_2.product_qty)
        self.assert_response(
            response, next_state="select_move", data=self._data_for_select_move(picking)
        )
        # Now, user1 can start working on this again
        service_user_1.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
