# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSelectDestPackage(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        package_model = cls.env["stock.quant.package"]
        cls.package = package_model.create(
            {
                "name": "FOO",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls.input_sublocation = (
            cls.env["stock.location"]
            .sudo()
            .create({"name": "Input A", "location_id": cls.input_location.id})
        )

    def test_scan_new_package(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FooBar",
            },
        )
        # Package doesn't exist, odoo asks for a confirmation to create it
        self.assertFalse(selected_move_line.result_package_id)
        self.assert_response(
            response,
            next_state="confirm_new_package",
            data={
                "picking": self._data_for_picking_with_moves(picking),
                "selected_move_line": self.data.move_lines(selected_move_line),
                "new_package_name": "FooBar",
            },
            message={
                "message_type": "warning",
                "body": ("Create new PACK FooBar? " "Scan it again to confirm."),
            },
        )
        # Try again with confirmation = True
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FooBar",
                "confirmation": True,
            },
        )
        self.assertEqual(selected_move_line.result_package_id.name, "FooBar")
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
        )

    def test_scan_not_empty_package(self):
        self._update_qty_in_location(
            self.packing_location, self.product_a, 10, package=self.package
        )
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # Assigning a package to a different move line
        # so that the package is available for the picking.
        different_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_b
        )
        different_move_line.result_package_id = self.package
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FOO",
            },
        )
        self.assertFalse(selected_move_line.result_package_id.name)
        picking_data = self.data.picking(picking)
        package_data = self.data.packages(
            self.package.with_context(picking_id=picking.id),
            picking=picking,
            with_packaging=True,
        )
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": picking_data,
                "packages": package_data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
            message={
                "message_type": "warning",
                "body": "Package FOO is not empty.",
            },
        )

    def test_scan_existing_package(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # Assigning a package to a different move line
        # so that the package is available for the picking.
        different_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_b
        )
        self.package.location_id = self.input_sublocation
        different_move_line.result_package_id = self.package
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FOO",
            },
        )
        self.assertEqual(selected_move_line.result_package_id.name, self.package.name)
        self.assertEqual(selected_move_line.location_dest_id, self.input_sublocation)
        self.assert_response(
            response,
            next_state="select_move",
            data=self._data_for_select_move(picking),
        )
