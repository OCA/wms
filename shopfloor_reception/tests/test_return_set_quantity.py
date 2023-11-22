# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .reception_return_common import CommonCaseReturn


class TestSetQuantityReturn(CommonCaseReturn):
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

    def _dispatch(self, quantity=None, barcode=None):
        params = {
            "picking_id": self.return_picking.id,
            "selected_line_id": self.selected_move_line.id,
        }
        if barcode:
            params["barcode"] = barcode
        if quantity:
            params["quantity"] = quantity
        return self.service.dispatch(
            "set_quantity",
            params=params,
        )

    def _get_data(self):
        return {
            "confirmation_required": None,
            "picking": self.data.picking(self.return_picking),
            "selected_move_line": self.data.move_lines(self.selected_move_line),
        }

    def test_set_quantity(self):
        # Max allowed qty_done is 10.0
        response = self._dispatch(quantity=20.0)
        self.assertEqual(self.selected_move_line.qty_done, 20.0)
        self.assert_response(response, next_state="set_quantity", data=self._get_data())
        # Now, we try to set more qty_done that what's allowed.
        response = self._dispatch(quantity=21.0)
        # Qty done has been kept as it was
        self.assertEqual(self.selected_move_line.qty_done, 20.0)
        message = {
            "message_type": "error",
            "body": "You cannot return more quantity than what was initially sent.",
        }
        self.assert_response(
            response,
            next_state="set_quantity",
            data=self._get_data(),
            message=message,
        )

    def test_set_quantity_by_product(self):
        expected_qty = 1.0
        # Here, the max qty is 20.0, since this is the originally sent qty
        # We are allowed to increment qty 9 times
        for __ in range(19):
            response = self._dispatch(barcode=self.product.barcode)
            expected_qty += 1
            self.assertEqual(self.selected_move_line.qty_done, expected_qty)
            self.assert_response(
                response, next_state="set_quantity", data=self._get_data()
            )
        # Already tested, but make it explicit
        self.assertEqual(self.selected_move_line.qty_done, 20.0)
        # If we try once more, we should get an error
        response = self._dispatch(barcode=self.product.barcode)
        # We are not allowed to set qty_done 21.0, since the origin move's qty was 10.0
        self.assertEqual(self.selected_move_line.qty_done, 20.0)
        message = {
            "message_type": "error",
            "body": "You cannot return more quantity than what was initially sent.",
        }
        self.assert_response(
            response,
            next_state="set_quantity",
            data=self._get_data(),
            message=message,
        )

    def test_set_quantity_by_packaging(self):
        packaging = self.product_a_packaging
        response = self._dispatch(barcode=packaging.barcode)
        # By selecting the line by product, qty done was set to 1.0
        # Now, we increment by packaging_qty which is 10.0
        self.assertEqual(self.selected_move_line.qty_done, 11.0)
        self.assert_response(response, next_state="set_quantity", data=self._get_data())
        # Sent qty was 20.0. We cannot create a return with more returned qty
        # Therefore, qty isn't increased, and an error is returned
        response = self._dispatch(barcode=packaging.barcode)
        self.assertEqual(self.selected_move_line.qty_done, 11.0)
        message = {
            "message_type": "error",
            "body": "You cannot return more quantity than what was initially sent.",
        }
        self.assert_response(
            response,
            next_state="set_quantity",
            data=self._get_data(),
            message=message,
        )
