# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.shopfloor.tests.test_checkout_base import CheckoutCommonCase
from odoo.addons.shopfloor.tests.test_checkout_select_package_base import (
    CheckoutSelectPackageMixin,
)


class CheckoutPutInPackRestriction(CheckoutCommonCase, CheckoutSelectPackageMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.carrier = cls.env.ref("delivery.normal_delivery_carrier")
        cls.picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
            ]
        )
        cls.pack1_moves = cls.picking.move_lines[:3]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls.picking.action_assign()

    def test_select_line_putinpack_restriction_no_package(self):
        """Check info for put in pack restriction is passed to select_package state."""
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "no_package"
        selected_lines = self.picking.move_line_ids
        pack = self.picking.move_line_ids.package_id
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                "package_id": pack.id,
            },
        )
        self._assert_selected(
            response,
            selected_lines,
            no_package_enabled=True,
            package_allowed=False,
        )

    def test_select_line_putinpack_restriction_with_package(self):
        """Check info for put in pack restriction is passed to select_package state."""
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "with_package"
        selected_lines = self.picking.move_line_ids
        pack = self.picking.move_line_ids.package_id
        response = self.service.dispatch(
            "select_line",
            params={
                "picking_id": self.picking.id,
                "package_id": pack.id,
            },
        )
        self._assert_selected(
            response,
            selected_lines,
            no_package_enabled=False,
            package_allowed=True,
        )

    def test_scan_package_action_restriction_no_package(self):
        """Check scanning a package with a no package restriction."""
        self.picking.sudo().picking_type_id.put_in_pack_restriction = "no_package"
        move = self.picking.move_lines
        selected_line = move.move_line_ids
        other_package = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "scan_package_action",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": selected_line.ids,
                "barcode": other_package.name,
            },
        )
        data = self.service._data_response_for_select_package(
            self.picking, selected_line
        )
        message = self.service.msg_store.package_not_allowed_for_operation()
        self.assert_response(
            response, next_state="select_package", message=message, data=data
        )
