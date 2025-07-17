# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from unittest import mock

from odoo.addons.shopfloor_printing_base.components.printing import (
    ShopFloorPrintingAction,
)
from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestSetDestinationPrinting(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        cls.location_dest = cls.env.ref("stock.stock_location_stock")

    def test_print_labels(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        with mock.patch.object(ShopFloorPrintingAction, "print") as mock_print:
            mock_print.return_value = True
            response = self.service.dispatch(
                "print_labels",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "quantity": 2,
                },
            )
            mock_print.assert_called_once()
            message = {"message_type": "success", "body": "Print job sent"}
            self.assertEqual(
                message,
                message | response.get("message"),
            )

    def test_print_labels_error(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        with mock.patch.object(ShopFloorPrintingAction, "print") as mock_print:
            mock_print.return_value = False
            response = self.service.dispatch(
                "print_labels",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "quantity": 2,
                },
            )
            mock_print.assert_called_once()
            message = {"message_type": "warning", "body": "Printing error"}
            self.assertEqual(
                message,
                message | response.get("message"),
            )
