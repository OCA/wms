# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from odoo import fields

from .common import CommonCase


class TestSelectLine(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a.tracking = "lot"

    def test_scan_barcode_not_found(self):
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_line", params={"picking_id": picking.id, "barcode": "NOPE"}
        )
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def test_scan_product(self):
        picking = self._create_picking()
        self.assertFalse(picking.printed)
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        data = self.data.picking(picking)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assertTrue(selected_move_line.picking_id.printed)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_product_partial(self):
        # Scan a line
        # Set a partial quantity done
        # Try to scan the product again
        # The selected line should be the other one
        picking = self._create_picking()
        lot = self._create_lot()
        self.assertFalse(picking.printed)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )

        # Activate INPUT location
        selected_move_line.location_dest_id.sudo().active = True

        selected_move_line.lot_id = lot
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": lot.name},
        )
        data = self.data.picking(picking)

        self.assertTrue(selected_move_line.picking_id.printed)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 5.0,
            },
        )

        response = self.service.dispatch(
            "process_without_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 5.0,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation": None,
            },
        )

        response = self.service.dispatch(
            "set_destination",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "location_name": "INPUT",
            },
        )
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
        )
        lines = picking.move_line_ids.filtered(lambda l: l.product_id == self.product_a)
        self.assertEqual(2, len(lines))
        previous_line = selected_move_line

        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": lot.name},
        )

        self.assertNotEqual(
            previous_line.id,
            response["data"]["set_quantity"]["selected_move_line"][0]["id"],
        )

    def test_scan_packaging(self):
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        data = self.data.picking(picking)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_lot(self):
        picking = self._create_picking()
        lot = self._create_lot()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.lot_id = lot
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": lot.name,
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
        )

    def test_scan_lot_concurrent(self):
        """
        If 2 operators work on the same lot, the second operator
        should not steal the move line of the first.
        """
        picking = self._create_picking()
        lot = self._create_lot()

        service_u1 = self.service
        res_u1 = service_u1.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": lot.name,
            },
        )
        # User 2 starts working on the same move
        service_u2 = self._get_service_for_user(self.shopfloor_manager)
        res_u2 = service_u2.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": lot.name,
            },
        )
        self.assertNotEqual(
            res_u1["data"]["set_quantity"]["selected_move_line"][0]["id"],
            res_u2["data"]["set_quantity"]["selected_move_line"][0]["id"],
        )

    def test_scan_not_tracked_product(self):
        self.product_a.tracking = "none"
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        data = self.data.picking(picking)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    def test_scan_not_tracked_packaging(self):
        self.product_a.tracking = "none"
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        data = self.data.picking(picking)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    def test_scan_product_not_found(self):
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_c.barcode},
        )
        error_msg = "Product not found in the current transfer or already in a package."
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
            message={"message_type": "warning", "body": error_msg},
        )

    def test_scan_packaging_not_found(self):
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_c_packaging.barcode,
            },
        )
        error_msg = (
            "Packaging not found in the current transfer or already in a package."
        )
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
            message={"message_type": "warning", "body": error_msg},
        )

    def test_assign_shopfloor_user_to_line(self):
        picking = self._create_picking()
        for line in picking.move_line_ids:
            self.assertEqual(line.shopfloor_user_id.id, False)
        self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_a.barcode,
            },
        )
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        other_move_line = fields.first(
            picking.move_line_ids.filtered(lambda l: l.product_id != self.product_a)
        )
        self.assertEqual(selected_move_line.shopfloor_user_id.id, self.env.uid)
        self.assertEqual(other_move_line.shopfloor_user_id.id, False)

    def test_create_new_line_none_available(self):
        # If there's already a move line for a given incoming move,
        # we assigned the whole move's product_uom_qty to it.
        # The reason for that is that when recomputing states for a given move
        # if sum(move.move_line_ids.reserved_uom_qty) != move.product_uom_qty,
        # then it's state won't be assigned.
        # For instance:
        #   - user 1 selects line1
        #   - user 2 selected line1 too
        #   - user 1 posts 20/40 goods
        #   - user 2 tries to process any qty, and it fails, because posting
        #     a move triggers the recompute of move's state
        # To avoid that, the first created line gets
        # product_uom_qty = move.product_uom_qty
        # The next ones are getting 0.
        picking = self._create_picking()
        self.assertEqual(len(picking.move_line_ids), 2)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # The picking and the selected line have been previously assigned to a different user
        # and this user has completed a total of 3 units.
        another_user = fields.first(
            self.env["res.users"].search([("id", "!=", self.env.uid)])
        )
        selected_move_line.shopfloor_user_id = another_user
        selected_move_line.qty_done = 3
        # When the user scans that product,
        # a new line will be generated with the remaining qty todo.
        self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_a.barcode,
            },
        )
        # A new line has been created
        self.assertEqual(len(picking.move_line_ids), 3)
        created_line = picking.move_line_ids[2]
        # And its product_uom_qty is 0
        self.assertEqual(created_line.reserved_uom_qty, 0.0)
        self.assertEqual(created_line.shopfloor_user_id.id, self.env.uid)

    def test_done_action(self):
        picking = self._create_picking()

        # These are needed to test that we get a valid list of pickings
        # when returning to select_document.
        self._create_picking(
            picking_type=picking.picking_type_id, scheduled_date=fields.Datetime.today()
        )
        self._create_picking(
            picking_type=picking.picking_type_id, scheduled_date=fields.Datetime.today()
        )

        for line in picking.move_line_ids:
            line.qty_done = line.reserved_uom_qty
            lot = (self._create_lot(product_id=line.product_id.id),)
            line.lot_id = lot
        # Ask for confirmation to mark the package as done.
        response = self.service.dispatch(
            "done_action",
            params={
                "picking_id": picking.id,
            },
        )
        data = {"picking": self._data_for_picking_with_moves(picking)}
        self.assert_response(
            response,
            next_state="confirm_done",
            data=data,
            message={"message_type": "warning", "body": "Are you sure?"},
        )
        # Confirm the package is done.
        response = self.service.dispatch(
            "done_action",
            params={
                "picking_id": picking.id,
                "confirmation": True,
            },
        )
        pickings = self.env["stock.picking"].search(
            [
                ("state", "=", "assigned"),
                ("picking_type_id", "=", picking.picking_type_id.id),
                ("user_id", "=", False),
                ("scheduled_date", "=", fields.Datetime.today()),
            ],
            order="scheduled_date ASC, id ASC",
        )
        message = "Transfer {} done".format(picking.name)
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(pickings)},
            message={"message_type": "success", "body": message},
        )

    def test_manual_select_move(self):
        picking = self._create_picking()
        selected_move = picking.move_ids.filtered(
            lambda m: m.product_id == self.product_a
        )
        response = self.service.dispatch(
            "manual_select_move",
            params={"move_id": selected_move.id},
        )
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_select_move_next_state_ignores_lot_name(self):
        picking = self._create_picking()

        self.product_a.tracking = "lot"
        self.product_b.tracking = "lot"

        move_a = picking.move_ids.filtered(lambda m: m.product_id == self.product_a)
        move_line_a = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        move_line_a.lot_id = self._create_lot()

        move_b = picking.move_ids.filtered(lambda m: m.product_id == self.product_b)
        move_line_b = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_b
        )
        move_line_b.lot_name = "Pre-Configured Lot Name"
        self._create_lot(
            product_id=self.product_b.id,
            name="Pre-Configured Lot Name",
            expiration_date="2020-02-02 12:00:00",
        )

        # There is already a lot -> we skip "set_lot"
        response_a = self.service.dispatch(
            "manual_select_move",
            params={"move_id": move_a.id},
        )
        self.assertEqual(response_a.get("next_state"), "set_quantity")

        # There is a lot name but no lot record -> enter "set_lot"
        response_b = self.service.dispatch(
            "manual_select_move",
            params={"move_id": move_b.id},
        )
        self.assertEqual(response_b.get("next_state"), "set_lot")

        # The UI should receive the lot metadata so as to be able to prefill
        self.assertEqual(
            response_b["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"],
            "Pre-Configured Lot Name",
        )
        self.assertEqual(
            response_b["data"]["set_lot"]["selected_move_line"][0]["lot"][
                "expiration_date"
            ],
            "2020-02-02T12:00:00",
        )
