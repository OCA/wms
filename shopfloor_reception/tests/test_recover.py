# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

# Recover happens at line selection.
# If a line exists for current user

from .common import CommonCase


class TestRecover(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.recover_msg = {
            "message_type": "info",
            "body": "Recovered previous session.",
        }

    def test_recover(self):
        # here, product isn't tracked by lot, but the move has a move
        # line already assigned to the user.
        # No quantity done, we should be redirected to set_quantity,
        # with the default qty set
        picking = self._create_picking()
        # First time we select the line, no recover
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        selected_move_line = picking.move_line_ids.filtered(
            lambda li: li.product_id == self.product_a
        )
        self.assertEqual(selected_move_line.qty_done, 1)
        self.assertEqual(selected_move_line.shopfloor_user_id.id, self.env.uid)
        picking_data = self.data.picking(picking)
        move_line_data = self.data.move_lines(selected_move_line)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
                "confirmation_required": None,
            },
        )
        # Now that there's a shopfloor_user_id, we should recover the session
        # but since didn't change anything, nothing should change.
        # Most importantly, the existing move_line should be reused throughout
        # the whole process
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        # qty done is the same
        self.assertEqual(selected_move_line.qty_done, 1)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
                "confirmation_required": None,
            },
            message=self.recover_msg,
        )
        # Set qty_done to 5/10 on the move line, we should recover it
        selected_move_line.qty_done = 5
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        self.assertEqual(selected_move_line.qty_done, 5)
        move_line_data = self.data.move_lines(selected_move_line)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
                "confirmation_required": None,
            },
            message=self.recover_msg,
        )
        # If the goods were put in a pack, we move to set destination
        response = self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": selected_move_line.qty_done,
            },
        )
        package = selected_move_line.result_package_id
        self.assertTrue(package)
        self.assertEqual(selected_move_line.qty_done, 5)
        self.assertEqual(selected_move_line.reserved_uom_qty, 5)
        picking_data = self.data.picking(picking)
        move_line_data = self.data.move_lines(selected_move_line)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
                "confirmation": None,
            },
        )
        # Scan the line again, we should end up with the exact same result
        # with the additionnal recover message
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
                "confirmation": None,
            },
            message=self.recover_msg,
        )

    def test_recover_tracking_by_lot(self):
        # exact same test, just showing that we skip the set lot when recovering
        picking = self._create_picking()
        self.product_a.tracking = "lot"
        # First time we select the line, no recover
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        selected_move_line = picking.move_line_ids.filtered(
            lambda li: li.product_id == self.product_a
        )
        picking_data = self.data.picking(picking)
        move_line_data = self.data.move_lines(selected_move_line)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
            },
        )
        # Scan the same line, we end up on the same screen, but with a recover msg
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
            },
            message=self.recover_msg,
        )
        # Set a lot to the move line, we recover again, but straight to set quantity.
        selected_move_line.lot_id = self._create_lot()
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.default_code},
        )
        move_line_data = self.data.move_lines(selected_move_line)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": picking_data,
                "selected_move_line": move_line_data,
                "confirmation_required": None,
            },
            message=self.recover_msg,
        )
        # The rest is all the same as test_recover
