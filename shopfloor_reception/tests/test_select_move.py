# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

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
                "selected_move_line": self.data.move_lines(selected_move_line),
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
                "selected_move_line": self.data.move_lines(selected_move_line),
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

    def test_assign_user_to_picking(self):
        picking = self._create_picking()
        self.assertEqual(picking.user_id.id, False)
        self.service.dispatch(
            "scan_line",
            params={
                "picking_id": picking.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assertEqual(picking.user_id.id, self.env.uid)

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
        # If all lines for a product are already assigned to a different user
        # and there's still qty todo remaining
        # a new line will be created for that qty todo.
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
        self.assertEqual(len(picking.move_line_ids), 3)
        created_line = picking.move_line_ids[2]
        self.assertEqual(created_line.product_uom_qty, 7)
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
            line.qty_done = line.product_uom_qty
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
