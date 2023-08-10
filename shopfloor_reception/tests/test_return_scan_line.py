# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .reception_return_common import CommonCaseReturn


class TestScanLineReturn(CommonCaseReturn):
    def test_scan_product_not_in_delivery(self):
        self._enable_allow_return()
        delivery = self.create_delivery()
        self.deliver(delivery)
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        return_picking = self.get_new_pickings()
        wrong_product = self.product_b
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": return_picking.id, "barcode": wrong_product.barcode},
        )
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(return_picking)},
            message={
                "message_type": "error",
                "body": "Product is not in the current transfer.",
            },
        )

    def test_scan_product_in_delivery(self):
        self._enable_allow_return()
        delivery = self.create_delivery()
        self.deliver(delivery)
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        return_picking = self.get_new_pickings()
        product = self.product
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": return_picking.id, "barcode": product.barcode},
        )
        data = self.data.picking(return_picking)
        selected_move_line = self.get_new_move_lines()
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "confirmation_required": None,
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )
        self.assertEqual(selected_move_line.qty_done, 1.0)

    def test_scan_packaging_not_in_delivery(self):
        self._enable_allow_return()
        self._add_package_to_order(self.order)
        delivery = self.create_delivery()
        self.deliver(delivery)
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        return_picking = self.get_new_pickings()
        wrong_packaging = self.product_b_packaging
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": return_picking.id,
                "barcode": wrong_packaging.barcode,
            },
        )
        self.assert_response(
            response,
            next_state="select_move",
            data={"picking": self._data_for_picking_with_moves(return_picking)},
            message={
                "message_type": "warning",
                "body": "Packaging not found in the current transfer.",
            },
        )

    def test_scan_packaging_in_delivery(self):
        self._enable_allow_return()
        delivery = self.create_delivery()
        self.deliver(delivery)
        self.service.dispatch("scan_document", params={"barcode": self.order.name})
        return_picking = self.get_new_pickings()
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": return_picking.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        selected_move_line = self.get_new_move_lines()
        move_line_data = self.data.move_lines(selected_move_line)
        move_line_data[0]["quantity"] = 20.0
        # Displayed qtu todo is modified by _align_display_product_uom_qty
        data = self.data.picking(return_picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "confirmation_required": None,
                "picking": data,
                "selected_move_line": move_line_data,
            },
        )
        self.assertEqual(selected_move_line.qty_done, self.product_a_packaging.qty)
