# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSelectDestPackage(CommonCase):
    def test_set_done_no_backorder(self):
        picking = self._create_picking()
        picking.move_line_ids.write({"qty_done": 10, "shopfloor_checkout_done": True})
        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        # User is asked to confirm the action
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
            message={"message_type": "warning", "body": "Are you sure?"},
        )
        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id, "confirmation": True}
        )
        self.assertEqual(picking.state, "done")
        # No more picking to process. Success message
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "message_type": "success",
                "body": f"Transfer {picking.name} done",
            },
        )

    def test_set_done_no_qty_processed(self):
        picking = self._create_picking()
        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
            message={
                "message_type": "warning",
                "body": "No quantity has been processed, unable to complete the transfer.",
            },
        )

    def test_set_done_with_backorder(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.qty_done = 10.0
        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id}
        )
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
            message={
                "message_type": "warning",
                "body": (
                    "Not all lines have been processed with full quantity. "
                    "Do you confirm partial operation?"
                ),
            },
        )
        response = self.service.dispatch(
            "done_action", params={"picking_id": picking.id, "confirmation": True}
        )
        self.assertEqual(picking.state, "done")
        backorder = picking.backorder_ids
        self.assertEqual(backorder.move_line_ids.product_id, self.product_b)
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self.data.pickings(backorder)},
            message={
                "message_type": "success",
                "body": f"Transfer {picking.name} done",
            },
        )
