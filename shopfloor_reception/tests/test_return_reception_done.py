# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .reception_return_common import CommonCaseReturn


class TestReturn(CommonCaseReturn):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._enable_allow_return()
        delivery = cls.create_delivery()
        cls.deliver(delivery)

    def setUp(self):
        super().setUp()
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        self.return_picking = self.get_new_pickings()
        product = self.product
        self.service.dispatch(
            "scan_line",
            params={"picking_id": self.return_picking.id, "barcode": product.barcode},
        )
        self.selected_move_line = self.get_new_move_lines()

    def _set_quantity_done(self, qty_done=20):
        params = {
            "picking_id": self.return_picking.id,
            "selected_line_id": self.selected_move_line.id,
            "quantity": qty_done,
        }
        self.service.dispatch("set_quantity", params=params)

    def _dispatch(self, confirmation=False):
        params = {"picking_id": self.return_picking.id, "confirmation": confirmation}
        response = self.service.dispatch("done_action", params=params)
        # Here, since we receive goods in input location, which triggers creation of
        # an internal shipping, sending goods from input to stock.
        # This isn't related to the reception scenario, we do not want
        # those internal shippings to be retrieved with `get_new_pickings`.
        self.cache_existing_record_ids()
        return response

    def test_set_done_full_qty_done(self):
        self._set_quantity_done()
        response = self._dispatch()
        self.assertEqual(self.return_picking.state, "done")
        # No more picking to process. Success message
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "message_type": "success",
                "body": f"Transfer {self.return_picking.name} done",
            },
        )

    def test_set_done_partial_qty_done(self):
        self.assertEqual(self.selected_move_line.product_uom_qty, 20.0)
        self._set_quantity_done(qty_done=10.0)
        response = self._dispatch()
        # As this is a return created by the app, no backorder is created,
        # even if qty_done doesn't match que product_uom_qty
        self.assertEqual(self.return_picking.state, "done")
        self.assertEqual(self.selected_move_line.qty_done, 10.0)
        self.assertFalse(bool(self.return_picking.backorder_ids))
        # Success message
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "message_type": "success",
                "body": f"Transfer {self.return_picking.name} done",
            },
        )
        # Now, since we still have returned 10 units out of ten, try to return
        # the next ones
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        return_picking_2 = self.get_new_pickings()
        self.service.dispatch(
            "scan_line",
            params={"picking_id": return_picking_2.id, "barcode": self.product.barcode},
        )
        selected_line_2 = self.get_new_move_lines()
        # Ensure that the max qty to return is 10.0
        self.assertEqual(selected_line_2.product_uom_qty, 10.0)
        # Set qty done == 10.0
        params = {
            "picking_id": return_picking_2.id,
            "selected_line_id": selected_line_2.id,
            "quantity": 10.0,
        }
        self.service.dispatch("set_quantity", params=params)
        # Set to done
        params = {"picking_id": return_picking_2.id}
        response = self.service.dispatch("done_action", params=params)
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={
                "message_type": "success",
                "body": f"Transfer {return_picking_2.name} done",
            },
        )

    def test_already_returned(self):
        # Set return move as completely done (20/20)
        self._set_quantity_done()
        # Confirm return picking
        response = self._dispatch()
        # Select the same document again
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        second_return_picking = self.get_new_pickings()
        # Now, try to select a product that has already been completely returned
        product = self.product
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": second_return_picking.id, "barcode": product.barcode},
        )
        expected_message = {
            "message_type": "error",
            "body": "The product/packaging you selected has already been returned.",
        }
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(second_return_picking)},
            message=expected_message,
        )
