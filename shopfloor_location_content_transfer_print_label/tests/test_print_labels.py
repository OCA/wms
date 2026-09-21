# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from unittest import mock

from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)
from odoo.addons.shopfloor_printing_base.components.printing import (
    ShopFloorPrintingAction,
)


class TestSetDestinationPrinting(LocationContentTransferCommonCase):
    def test_print_labels(self):
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_ids)
        picking.action_assign()
        move_lines = picking.move_line_ids

        with mock.patch.object(ShopFloorPrintingAction, "print") as mock_print:
            mock_print.return_value = True
            response = self.service.print_labels(
                move_line_ids=move_lines.ids, quantity=10
            )

            # Assert mock was called
            mock_print.assert_called_once_with(record_ids=move_lines.ids, quantity=10)

            # Assert response
            self.assertIn("message", response)
            self.assertEqual(
                response["message"], self.service.msg_store.print_job_sent()
            )

    def test_print_labels_error(self):
        # Simulate move lines without picking
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_ids)
        picking.action_assign()
        move_lines = picking.move_line_ids

        with mock.patch.object(ShopFloorPrintingAction, "print") as mock_print:
            mock_print.return_value = False
            response = self.service.print_labels(
                move_line_ids=move_lines.ids, quantity=10
            )

            # Assert mock was called
            mock_print.assert_called_once_with(record_ids=move_lines.ids, quantity=10)

            # Assert response
            self.assertIn("message", response)
            self.assertEqual(response["message"], self.service.msg_store.print_error())
