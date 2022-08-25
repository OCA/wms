# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

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
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def test_scan_product(self):
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
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
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
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
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
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
                "selected_move_lines": self.data.move_lines(selected_move_line),
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
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_product_not_found(self):
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_c.barcode},
        )
        error_msg = "Product is not in the current transfer."
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
            message={"message_type": "error", "body": error_msg},
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
        error_msg = "Packaging is not in the current transfer."
        data = self.data.picking(picking)
        data.update({"move_lines": self.data.move_lines(picking.move_line_ids)})
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": data},
            message={"message_type": "error", "body": error_msg},
        )
