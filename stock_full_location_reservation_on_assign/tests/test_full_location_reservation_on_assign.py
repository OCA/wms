# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.stock_full_location_reservation.tests.common import (
    TestStockFullLocationReservationCommon,
)


class TestFullLocationReservationOnAssign(TestStockFullLocationReservationCommon):
    def test_full_location_reservation_on_assign(self):
        self.picking_type.auto_full_location_reservation_on_assign = True
        self._create_quants(
            [
                (self.productA, self.location_rack_child, 10.0),
                (self.productB, self.location_rack_child, 10.0),
            ]
        )
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 5]],
        )

        picking.action_confirm()
        self._check_move_line_len(picking, 1)
        picking.action_assign()

        self._check_move_line_len(picking, 3)
        self._check_move_line_len(picking, 2, self._filter_func)
