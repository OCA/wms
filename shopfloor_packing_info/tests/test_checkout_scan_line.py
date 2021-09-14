# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.addons.shopfloor.tests.test_checkout_scan_line_base import (
    CheckoutScanLineCaseBase,
)


class CheckoutScanLineCase(CheckoutScanLineCaseBase):
    def test_scan_line_package_ok_packing_info_filled_info(self):
        picking = self._create_picking(
            lines=[(self.product_a, 10), (self.product_b, 10)]
        )
        packing_info_text = "Please do it like this!"
        shopfloor_packing_info = (
            self.env["shopfloor.packing.info"]
            .sudo()
            .create({"name": "Test", "text": packing_info_text})
        )
        picking.sudo().partner_id.shopfloor_packing_info_id = shopfloor_packing_info
        picking.sudo().picking_type_id.shopfloor_display_packing_info = True
        move1 = picking.move_lines[0]
        move2 = picking.move_lines[1]
        # put the lines in 2 separate packages (only the first line should be selected
        # by the package barcode)
        self._fill_stock_for_moves(move1, in_package=True)
        self._fill_stock_for_moves(move2, in_package=True)
        picking.action_assign()
        move_line = move1.move_line_ids
        self._test_scan_line_ok(
            move_line.package_id.name, move_line, packing_info=packing_info_text
        )
