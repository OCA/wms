# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.stock_full_location_reservation.tests.common import (
    TestStockFullLocationReservationCommon,
)


class TestFullLocationReservation(TestStockFullLocationReservationCommon):
    def test_full_location_reservation(self):
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 5]],
        )

        picking.action_confirm()
        self._check_move_line_len(picking, 1)

        picking.do_full_location_reservation()
        self._check_move_line_len(picking, 1)

        self._create_quants(
            [
                (self.productA, self.location_rack_child, 10.0),
                (self.productB, self.location_rack_child, 10.0),
            ]
        )

        picking.do_full_location_reservation()
        self._check_move_line_len(picking, 1)

        picking.action_assign()

        picking.do_full_location_reservation()

        self._check_move_line_len(picking, 3)
        self._check_move_line_len(picking, 2, self._filter_func)

        # repeat test to check undo in do
        picking.do_full_location_reservation()

        self._check_move_line_len(picking, 3)
        self._check_move_line_len(picking, 2, self._filter_func)

        moves = picking.move_ids.filtered(self._filter_func)
        self.assertEqual(moves.location_id, self.location_rack_child)

        picking.undo_full_location_reservation()

        self._check_move_line_len(picking, 1)
        self._check_move_line_len(picking, 0, self._filter_func)

    def test_multiple_pickings(self):
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 1]],
        )

        picking2 = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 1]],
        )

        pickings = picking | picking2

        self._create_quants(
            [
                (self.productA, self.location_rack_child, 10.0),
                (self.productB, self.location_rack_child, 10.0),
            ]
        )

        pickings.action_confirm()
        pickings.action_assign()

        pickings.do_full_location_reservation()
        self._check_move_line_len(pickings, 4)
        self._check_move_line_len(pickings, 2, self._filter_func)

    def test_package_only(self):
        package = self.env["stock.quant.package"].create({"name": "test package"})
        self._create_quants(
            [
                (self.productA, self.location_rack_child, 10.0),
                (self.productA, self.location_rack_child, 10.0, package),
            ]
        )
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [
                [self.productA, 1],
                [self.productA, 1, package],
            ],
        )
        picking.action_confirm()
        picking.action_assign()

        self.assertEqual(picking.move_line_ids.package_id, package)
        self._check_move_line_len(picking, 2)
        picking.move_ids._full_location_reservation(package_only=True)
        self._check_move_line_len(picking, 3)
        self.assertEqual(picking.move_line_ids.package_id, package)
        self.assertEqual(sum(picking.move_line_ids.mapped("reserved_qty")), 11)

    def test_full_location_reservation_merge(self):
        """
        Activate the merge for new quantity move.
        Create a picking and confirm it (quantity: 5).
        Set product A in rack location (qauntity : 10).
        Confirm the picking.
        Do the full reservation.
        The whole quantity should be assigned in one move.

        """
        self.picking_type.merge_move_for_full_location_reservation = True
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 5]],
        )

        picking.action_confirm()
        self._check_move_line_len(picking, 1)

        self._create_quants(
            [
                (self.productA, self.location_rack_child, 10.0),
            ]
        )

        picking.action_assign()

        picking.do_full_location_reservation()

        self._check_move_line_len(picking, 1)
        self.assertEqual(10.0, picking.move_ids.product_uom_qty)
        self.assertEqual(10.0, picking.move_ids.reserved_availability)
