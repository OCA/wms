# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestShopfloorReceptionPutinpackRestriction(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        res = super().setUpClassBaseData()
        cls.picking = cls._create_picking()
        cls.selected_move_line = cls.picking.move_line_ids.filtered(
            lambda line: line.product_id == cls.product_a
        )
        return res

    def test_process_with_existing_package_not_allowed(self):
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "no_package"

        self.env["stock.quant.package"].create({"name": "FOO"})
        response = self.service.dispatch(
            "process_with_existing_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 2,
            },
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(self.selected_move_line),
                "confirmation_required": None,
                "put_in_pack_restriction": "no_package",
            },
            message=self.msg_store.package_not_allowed_for_operation(self.picking),
        )

    def test_process_with_new_package_not_allowed(self):
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "no_package"

        response = self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 2,
            },
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(self.selected_move_line),
                "confirmation_required": None,
                "put_in_pack_restriction": "no_package",
            },
            message=self.msg_store.package_not_allowed_for_operation(self.picking),
        )

    def test_process_without_package_not_allowed(self):
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "with_package"

        response = self.service.dispatch(
            "process_without_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 2,
            },
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(self.selected_move_line),
                "confirmation_required": None,
                "put_in_pack_restriction": "with_package",
            },
            message=self.msg_store.package_required_for_operation(self.picking),
        )

    def test_set_quantity_not_allowed(self):
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "no_package"

        self.env["stock.quant.package"].create({"name": "FOO"})
        # Simulates a scan of a package
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 0,
                "barcode": "FOO",
            },
        )

        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(self.selected_move_line),
                "confirmation_required": None,
                "put_in_pack_restriction": "no_package",
            },
            message=self.msg_store.package_not_allowed_for_operation(self.picking),
        )

    def test_set_quantity_scan_not_broken(self):
        """
        Ensure that the put in pack restriction does not prevent to update
        the quantity by scanning a product/packaging/location
        """
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "no_package"

        # Set qty by product barcode
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 0,
                "barcode": self.product_a.barcode,
            },
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(self.selected_move_line),
                "confirmation_required": None,
                "put_in_pack_restriction": "no_package",
            },
        )
        self.assertEqual(self.selected_move_line.qty_done, 1.0)

        # Set qty by packaging
        self.env["product.packaging"].sudo().create(
            {
                "name": "Box",
                "product_id": self.product_a.id,
                "qty": 5.0,
                "barcode": "PKG_TEST",
            }
        )
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 0,
                "barcode": "PKG_TEST",
            },
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(self.selected_move_line),
                "confirmation_required": None,
                "put_in_pack_restriction": "no_package",
            },
        )
        self.assertEqual(self.selected_move_line.qty_done, 5.0)

        # Set qty by location
        loc_dest = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Test Location",
                    "usage": "internal",
                    "location_id": self.picking.location_dest_id.id,
                }
            )
        )
        response = self.service.dispatch(
            "set_quantity",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 5,
                "barcode": loc_dest.name,
            },
        )
        self.assertIsNone(response.get("message"))
        self.assertEqual(self.selected_move_line.location_dest_id, loc_dest)
