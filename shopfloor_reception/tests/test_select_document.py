# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSelectDocument(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a.tracking = "lot"

    def test_scan_barcode_not_found(self):
        # next step is select_document, with an error message
        response = self.service.dispatch("scan_document", params={"barcode": "NOPE"})
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
            message={"message_type": "error", "body": "Barcode not found"},
        )

    def test_scan_picking_name(self):
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": picking.name}
        )
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": self._data_for_picking_with_line(picking)},
        )

    def test_scan_picking_origin(self):
        picking = self._create_picking()
        # Multiple pickings with this origin are found.
        # Return the filtered list of pickings.
        same_origin_picking = self._create_picking()
        picking.origin = "Somewhere together"
        same_origin_picking.origin = "Somewhere together"
        response = self.service.dispatch(
            "scan_document", params={"barcode": "Somewhere together"}
        )
        message = (
            "This source document is part of multiple pickings, please scan a package."
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings([same_origin_picking, picking])},
            message={
                "message_type": "warning",
                "body": message,
            },
        )

        # Only 1 picking with this origin is found.
        # Move to select_line.
        picking.origin = "Somewhere"
        response = self.service.dispatch(
            "scan_document", params={"barcode": "Somewhere"}
        )
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": self._data_for_picking_with_line(picking)},
        )

    def test_scan_packaging_single_picking(self):
        # next step is set_lot
        picking = self._create_picking()
        self._add_package(picking)
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a_packaging.barcode}
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

    def test_scan_product_single_picking(self):
        # next_step is set_lot
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a.barcode}
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

    def test_scan_not_tracked_product_single_picking(self):
        # next_step is set_quantity
        self.product_a.tracking = "none"
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a.barcode}
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
            },
        )

    def test_scan_packaging_multiple_pickings(self):
        # next step is select_document, with documents filtered based on the product
        p1 = self._create_picking()
        p2 = self._create_picking()
        self._add_package(p1)
        self._add_package(p2)
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a_packaging.barcode}
        )
        body = "Several transfers found, please select a transfer manually."
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(p1 | p2)},
            message={"message_type": "error", "body": body},
        )

    def test_scan_product_multiple_pickings(self):
        # next step is select_document, with documents filtered based on the packaging
        p1 = self._create_picking()
        p2 = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_a.barcode}
        )
        body = "Several transfers found, please select a transfer manually."
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(p1 | p2)},
            message={"message_type": "error", "body": body},
        )

    def test_scan_product_no_picking(self):
        # next_step is select_document, with an error message
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_c.barcode}
        )
        body = "No product found among current transfers."
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(picking)},
            message={"message_type": "warning", "body": body},
        )

    def test_scan_packaging_no_picking(self):
        # next step is select_document, with an error message
        picking = self._create_picking()
        response = self.service.dispatch(
            "scan_document", params={"barcode": self.product_c_packaging.barcode}
        )
        body = "No picking found for the scanned packaging."
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self._data_for_pickings(picking)},
            message={"message_type": "error", "body": body},
        )
