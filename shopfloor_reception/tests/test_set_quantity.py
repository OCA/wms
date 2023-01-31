# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetQuantity(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a_packaging.qty = 5.0
        cls.packing_location.sudo().active = True
        package_model = cls.env["stock.quant.package"]
        cls.package_without_location = package_model.create(
            {
                "name": "PKG_WO_LOCATION",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls.package_with_location = package_model.create(
            {
                "name": "PKG_W_LOCATION",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls.package_with_location_child_of_dest = package_model.create(
            {
                "name": "PKG_W_LOCATION_CHILD",
                "packaging_id": cls.product_a_packaging.id,
            }
        )
        cls._update_qty_in_location(
            cls.packing_location, cls.product_a, 10, package=cls.package_with_location
        )
        cls._update_qty_in_location(
            cls.dispatch_location,
            cls.product_a,
            10,
            package=cls.package_with_location_child_of_dest,
        )

    def test_set_quantity_scan_product(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 10.0,
                "barcode": selected_move_line.product_id.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 11.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_set_quantity_scan_packaging(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 10.0,
                "barcode": selected_move_line.product_id.packaging_ids.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 15.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_product(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 1.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )
        # Scan again, and ensure qty increments
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 4.0)

    def test_scan_packaging(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 5.0)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )
        # Scan again, and ensure qty increments
        self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.product_a_packaging.barcode,
            },
        )
        self.assertEqual(selected_move_line.qty_done, 10.0)

    def test_scan_package_with_destination_child_of_dest_location(self):
        # next step is select_move
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.package_with_location_child_of_dest.name,
            },
        )
        self.assertEqual(
            selected_move_line.result_package_id,
            self.package_with_location_child_of_dest,
        )
        self.assertEqual(selected_move_line.location_dest_id, self.dispatch_location)
        data = self.data.picking(picking, with_progress=True)
        data.update({"moves": self.data.moves(picking.move_lines)})
        self.assert_response(response, next_state="select_move", data={"picking": data})

    def test_scan_package_with_destination_not_child_of_dest_location(self):
        # next step is set_quantity with error
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.package_with_location.name,
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
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_scan_package_without_location(self):
        # next_step is set_destination
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.package_without_location.name,
            },
        )
        self.assertEqual(
            selected_move_line.result_package_id, self.package_without_location
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_scan_location_child_of_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        self.assertEqual(selected_move_line.location_dest_id, self.dispatch_location)
        data = self.data.picking(picking, with_progress=True)
        data.update({"moves": self.data.moves(picking.move_lines)})
        self.assert_response(response, next_state="select_move", data={"picking": data})

    def test_scan_location_not_child_of_dest_location(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": self.packing_location.barcode,
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
            message={"message_type": "error", "body": "You cannot place it here"},
        )

    def test_scan_new_package(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FooBar",
            },
        )
        picking_data = self.data.picking(picking)
        self.assertFalse(selected_move_line.result_package_id)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": picking_data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
            message={
                "message_type": "warning",
                "body": "Create new PACK FooBar? Scan it again to confirm.",
            },
        )
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "FooBar",
                "confirmation": True,
            },
        )
        self.assertEqual(selected_move_line.result_package_id.name, "FooBar")
        picking_data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": picking_data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )
