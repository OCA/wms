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

    def test_multi_lines_per_move(self):
        """
        We create :

            - Quantity of 10 on Rack of Product A
            - Quantity of 10 on Rack 2 of Product A
            - Quantity of 10 on Rack 3 of Product A

        We create a picking of 30 from parent Rack, all quantities should
        be reserved.

        Then, we update the Rack to 60 and we launch the full reservation
        on move 1.

        The moves lines should remains, the reserved total quantity should
        be 80 when the original demand should remain.

        """
        self.picking_type.merge_move_for_full_location_reservation = True
        self._create_quants(
            [
                (self.productA, self.location_rack_child, 10.0),
                (self.productA, self.location_rack_child_2, 10.0),
                (self.productA, self.location_rack_child_3, 10.0),
                (self.productB, self.location_rack_child, 15.0),
            ]
        )
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 30]],
        )
        picking.action_confirm()
        picking.action_assign()
        self.assertEqual(1, len(picking.move_ids))
        move_line_ids = picking.move_line_ids
        self.assertEqual(3, len(picking.move_line_ids))

        self._create_quants(
            [
                (self.productA, self.location_rack_child, 50.0),
            ]
        )

        self.assertEqual(
            60.0,
            self.productA.with_context(
                location=self.location_rack_child.id
            ).qty_available,
        )

        picking.move_line_ids[0]._full_location_reservation(reservation_mode="strict")

        self.assertEqual(3, len(picking.move_line_ids))

        self.assertEqual(
            move_line_ids,
            picking.move_line_ids,
        )
        self.assertEqual(picking.move_line_ids[0].reserved_uom_qty, 60.0)

        # The original demand stays at 30.0
        self.assertEqual(picking.move_ids.product_uom_qty, 30.0)
        self.assertEqual(picking.move_ids.reserved_availability, 80.0)

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
        picking.move_ids._full_location_reservation(reservation_mode="package")
        self._check_move_line_len(picking, 3)
        self.assertEqual(picking.move_line_ids.package_id, package)
        self.assertEqual(sum(picking.move_line_ids.mapped("reserved_qty")), 11)

    def test_product_mode(self):
        """
        Location has productA and productB.
        After product mode on a productA move: only productA gets a new
        full-reservation move — productB is left untouched.
        """
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
            [[self.productA, 1]],
        )
        picking.action_confirm()
        picking.action_assign()

        self._check_move_line_len(picking, 1)
        picking.move_ids._full_location_reservation(reservation_mode="product")
        # Original move + 1 new full-reservation move for remaining productA
        self._check_move_line_len(picking, 2)
        self._check_move_line_len(picking, 1, self._filter_func)
        full_reservation_moves = picking.move_ids.filtered(self._filter_func)
        self.assertEqual(full_reservation_moves.product_id, self.productA)
        # Total reserved = all 10 units of productA; productB untouched
        self.assertEqual(
            sum(picking.move_line_ids.mapped("reserved_uom_qty")),
            10.0,
        )

    def test_product_mode_multiple_packages(self):
        """
        Location has productA in two package combinations (packaged and
        unpackaged) plus productB. Move for productA (no package).
        After product mode: new moves are created for each package combination
        of productA — productB remains untouched.
        """
        package = self.env["stock.quant.package"].create({"name": "test package"})
        self._create_quants(
            [
                (self.productA, self.location_rack_child, 5.0),
                (self.productA, self.location_rack_child, 7.0, package),
                (self.productB, self.location_rack_child, 10.0),
            ]
        )
        picking = self._create_picking(
            self.location_rack,
            self.customer_location,
            self.picking_type,
            [[self.productA, 1]],
        )
        picking.action_confirm()
        picking.action_assign()

        self._check_move_line_len(picking, 1)
        picking.move_ids._full_location_reservation(reservation_mode="product")
        # Original move + 2 new full-reservation moves (one per package combo)
        self._check_move_line_len(picking, 3)
        self._check_move_line_len(picking, 2, self._filter_func)
        full_reservation_moves = picking.move_ids.filtered(self._filter_func)
        self.assertEqual(full_reservation_moves.product_id, self.productA)
        # Total reserved: 1 (original) + 4 (remaining no-pkg) + 7 (packaged) = 12
        self.assertEqual(
            sum(picking.move_line_ids.mapped("reserved_uom_qty")),
            12.0,
        )

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
        # The original demand remains the same
        self.assertEqual(10.0, picking.move_ids.product_uom_qty)
        self.assertEqual(10.0, picking.move_ids.reserved_availability)
