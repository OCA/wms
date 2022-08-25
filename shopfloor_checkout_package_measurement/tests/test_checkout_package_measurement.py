# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.shopfloor.tests.test_checkout_base import CheckoutCommonCase
from odoo.addons.shopfloor.tests.test_checkout_select_package_base import (
    CheckoutSelectPackageMixin,
)


class CheckoutPackageMeasurementCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "test.packaging",
                    "barcode": "PACKAGING",
                    "package_carrier_type": "none",
                }
            )
        )
        cls.carrier = cls.env.ref("delivery.normal_delivery_carrier")
        cls.packaging.sudo().package_height_required = True
        cls.picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
            ]
        )
        cls.picking.carrier_id = cls.carrier
        cls.pack1_moves = cls.picking.move_lines[:3]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls.picking.action_assign()

    def test_requested_measurement_for_new_package(self):
        """Check package measurement are requested for new package."""
        selected_lines = self.pack1_moves.move_line_ids
        move_line1, move_line2, move_line3 = selected_lines
        move_line1.qty_done = move_line1.product_uom_qty
        move_line2.qty_done = move_line2.product_uom_qty
        move_line3.qty_done = 0
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_lines.ids,
                "barcode": "PACKAGING",
            },
        )
        new_package = move_line1.result_package_id
        self.assert_response(
            response,
            next_state="package_measurement",
            data={
                "picking": self.data.picking(self.picking),
                "package": self.data.package(new_package, with_packaging=True),
                "package_requirement": self.data.package_requirement(self.packaging),
            },
        )

    def test_requested_measurement_for_existing_package(self):
        """Check measurement are requested for existing package."""
        selected_lines = self.pack1_moves.move_line_ids
        move_line1, move_line2, move_line3 = selected_lines
        move_line1.qty_done = move_line1.product_uom_qty

        # First have a new package created on the first line
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": move_line1.ids,
                "barcode": "PACKAGING",
            },
        )
        # Then assign the same package to the 2nd line
        new_package = move_line1.result_package_id
        # With the required measurement already set
        new_package.height = 23
        move_line2.qty_done = move_line2.product_uom_qty
        response = self.service.dispatch(
            "set_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": move_line2.ids,
                "package_id": new_package.id,
            },
        )
        # When adding to an existing package, the measurent screen needs to be
        # shown even when any required dimension is already set.
        # Because it probably needs to be updated.
        self.assert_response(
            response,
            next_state="package_measurement",
            data={
                "picking": self.data.picking(self.picking),
                "package": self.data.package(new_package, with_packaging=True),
                "package_requirement": self.data.package_requirement(self.packaging),
            },
        )

    def test_measurement_not_requested(self):
        """Check measurement are not requested if not required."""
        self.packaging.sudo().package_height_required = False
        selected_lines = self.pack1_moves.move_line_ids
        move_line1, move_line2, move_line3 = selected_lines
        # First have a new package created on the first line
        move_line1.qty_done = move_line1.product_uom_qty
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": move_line1.ids,
                "barcode": "PACKAGING",
            },
        )
        self.assertEqual(response["next_state"], "select_line")
        new_package = move_line1.result_package_id
        move_line2.qty_done = move_line2.product_uom_qty
        response = self.service.dispatch(
            "set_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": move_line2.ids,
                "package_id": new_package.id,
            },
        )
        self.assertEqual(response["next_state"], "select_line")

    def test_set_measurement_for_package(self):
        """Check package measurement are changed."""
        package = self.pack1_moves.move_line_ids.result_package_id
        response = self.service.dispatch(
            "set_package_measurement",
            params={
                "picking_id": self.picking.id,
                "package_id": package.id,
                "length": "23",
                "shipping_weight": "3.55",
            },
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "all_processed": False,
                "picking": self._stock_picking_data(self.picking, done=True),
            },
            message={"message_type": "success", "body": "Package measure(s) changed."},
        )
        self.assertEqual(package.pack_length, 23)
        self.assertEqual(package.shipping_weight, 3.55)
