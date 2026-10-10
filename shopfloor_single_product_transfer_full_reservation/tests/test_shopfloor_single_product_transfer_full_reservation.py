# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import CommonCase


class TestFullReservation(CommonCase):
    """Full reservation can be triggered from two entry points that share the same
    underlying logic:

    - automatic assignment: find_work -> _get_next_move_line_to_work
    - manual selection: scan_product -> _select_move_line_from_product
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # location_src_a: a single product, used to check that full_location_reservation
        # is applied (or not) depending on the menu option.
        cls._add_stock_to_product(cls.product_a, cls.location_src_a, 10)
        cls.picking_single_product = cls._create_picking(lines=[(cls.product_a, 5)])
        cls.picking_single_product.move_line_ids.sudo().location_dest_id = (
            cls.dispatch_location.id
        )

        # location_src_b: two different products, used to check that strict mode
        # does not spill over to another product at the same location.
        cls.location_src_b = (
            cls.env["stock.location"]
            .sudo()
            .create({"name": "Source B", "location_id": cls.location_src.id})
        )
        cls._add_stock_to_product(cls.product_a, cls.location_src_b, 10)
        cls._add_stock_to_product(cls.product_b, cls.location_src_b, 8)
        cls.picking_product_a = cls._create_picking(
            lines=[(cls.product_a, 5)], picking_type=cls.picking_type
        )
        cls.picking_product_a.move_line_ids.sudo().location_id = cls.location_src_b.id
        cls.picking_product_b = cls._create_picking(
            lines=[(cls.product_b, 3)], picking_type=cls.picking_type
        )
        cls.picking_product_b.move_line_ids.sudo().location_id = cls.location_src_b.id
        (
            cls.picking_product_a | cls.picking_product_b
        ).move_line_ids.sudo().location_dest_id = cls.dispatch_location.id

        # location_src_c: same (lot tracked) product, two different lots, used to
        # check that strict mode does not spill over to another lot.
        cls.location_src_c = (
            cls.env["stock.location"]
            .sudo()
            .create({"name": "Source C", "location_id": cls.location_src.id})
        )
        cls._set_product_tracking_by_lot(cls.product_c)
        cls.lot_1 = cls._create_lot_for_product(cls.product_c, "LOT-001")
        cls.lot_2 = cls._create_lot_for_product(cls.product_c, "LOT-002")
        cls._add_stock_to_product(cls.product_c, cls.location_src_c, 5, lot=cls.lot_1)
        cls._add_stock_to_product(cls.product_c, cls.location_src_c, 8, lot=cls.lot_2)
        cls.picking_lot = cls._create_picking(lines=[(cls.product_c, 2)])
        cls.picking_lot.move_line_ids.sudo().location_id = cls.location_src_c.id
        cls.picking_lot.move_line_ids.sudo().lot_id = cls.lot_1.id
        cls.picking_lot.move_line_ids.sudo().location_dest_id = cls.dispatch_location.id

    def test_no_full_reservation_find_work(self):
        self.menu.sudo().full_location_reservation = False
        move_line = self._find_work(self.picking_single_product)
        self.assertEqual(move_line.reserved_uom_qty, 5)
        self.assertEqual(move_line.location_id, self.location_src_a)

    def test_no_full_reservation_scan_product(self):
        self.menu.sudo().full_location_reservation = False
        self._scan_product(self.location_src_a, self.product_a.barcode)
        move_line = self.picking_single_product.move_line_ids
        self.assertEqual(move_line.reserved_uom_qty, 5)
        self.assertEqual(move_line.location_id, self.location_src_a)

    def test_full_reservation_find_work(self):
        self.menu.sudo().full_location_reservation = True
        self._find_work(self.picking_single_product)
        total_qty = sum(
            self.picking_single_product.move_line_ids.filtered(
                lambda l: l.product_id == self.product_a
                and l.location_id == self.location_src_a
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(total_qty, 10)

    def test_full_reservation_scan_product(self):
        self.menu.sudo().full_location_reservation = True
        self._scan_product(self.location_src_a, self.product_a.barcode)
        total_qty = sum(
            self.picking_single_product.move_line_ids.filtered(
                lambda l: l.product_id == self.product_a
                and l.location_id == self.location_src_a
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(total_qty, 10)

    def test_full_reservation_strict_does_not_overflow_to_other_product_find_work(self):
        self.menu.sudo().full_location_reservation = True
        self._find_work(self.picking_product_a)

        # product_a: full stock (10) must now be reserved.
        product_a_qty = sum(
            self.picking_product_a.move_line_ids.filtered(
                lambda l: l.product_id == self.product_a
                and l.location_id == self.location_src_b
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(product_a_qty, 10)

        # product_b: must remain at original reserved qty (3), not 8.
        product_b_qty = sum(
            self.picking_product_b.move_line_ids.filtered(
                lambda l: l.product_id == self.product_b
                and l.location_id == self.location_src_b
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(product_b_qty, 3)

    def test_full_reservation_strict_does_not_overflow_to_other_product_scan_product(
        self,
    ):
        self.menu.sudo().full_location_reservation = True
        self._scan_product(self.location_src_b, self.product_a.barcode)

        # product_a: full stock (10) must now be reserved.
        product_a_qty = sum(
            self.picking_product_a.move_line_ids.filtered(
                lambda l: l.product_id == self.product_a
                and l.location_id == self.location_src_b
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(product_a_qty, 10)

        # product_b: must remain at original reserved qty (3), not 8.
        product_b_qty = sum(
            self.picking_product_b.move_line_ids.filtered(
                lambda l: l.product_id == self.product_b
                and l.location_id == self.location_src_b
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(product_b_qty, 3)

    # -- strict mode: no overflow to other lots of the same product --

    def test_full_reservation_strict_does_not_overflow_to_other_lot_find_work(self):
        self.menu.sudo().full_location_reservation = True
        self._find_work(self.picking_lot)

        # lot_1: full stock at the location (5) must now be reserved.
        lot_1_qty = sum(
            self.picking_lot.move_line_ids.filtered(
                lambda l: l.lot_id == self.lot_1
                and l.location_id == self.location_src_c
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(lot_1_qty, 5)

        # lot_2: must remain unreserved
        lot_2_lines = self.env["stock.move.line"].search(
            [
                ("lot_id", "=", self.lot_2.id),
                ("location_id", "=", self.location_src_c.id),
            ]
        )
        self.assertFalse(lot_2_lines)

    def test_full_reservation_strict_does_not_overflow_to_other_lot_scan_product(self):
        self.menu.sudo().full_location_reservation = True
        # Product is tracked by lot: scan the lot barcode, not the product barcode.
        self._scan_product(self.location_src_c, self.lot_1.name)

        # lot_1: full stock at the location (5) must now be reserved.
        lot_1_qty = sum(
            self.picking_lot.move_line_ids.filtered(
                lambda l: l.lot_id == self.lot_1
                and l.location_id == self.location_src_c
            ).mapped("reserved_uom_qty")
        )
        self.assertEqual(
            lot_1_qty,
            5,
        )

        # lot_2: must remain unreserved
        lot_2_lines = self.env["stock.move.line"].search(
            [
                ("lot_id", "=", self.lot_2.id),
                ("location_id", "=", self.location_src_c.id),
            ]
        )
        self.assertFalse(lot_2_lines)
