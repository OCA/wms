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

    def test_scan_new_package(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "barcode": "FooBar",
            },
        )
        # Package doesn't exists, odoo asks for a confirmation to create it
        self.assertFalse(selected_move_line.result_package_id)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
            message={
                "message_type": "warning",
                "body": (
                    "Do you want to create package FooBar? " "Scan it again to confirm."
                ),
            },
        )
        # Try again with confirmation = True
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "barcode": "FooBar",
                "confirmation": True,
            },
        )
        self.assertEqual(selected_move_line.result_package_id.name, "FooBar")
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_not_empty_package(self):
        self._update_qty_in_location(
            self.packing_location, self.product_a, 10, package=self.package
        )
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "barcode": self.package.name,
            },
        )
        self.assertFalse(selected_move_line.result_package_id.name)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(selected_move_line),
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
        response = self.service.dispatch(
            "select_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": selected_move_line.ids,
                "barcode": self.package.name,
            },
        )
        self.assertEqual(selected_move_line.result_package_id.name, self.package.name)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(selected_move_line),
            },
        )
