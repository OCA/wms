# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import Form

from .common import CommonCase


# pylint: disable=missing-return
class TestActionsChangePackageLot(CommonCase):
    """Tests covering changing a package on a move line"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.work_on_actions(cls) as work:
            cls.change_package_lot = work.component(usage="change.package.lot")

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id
        cls.picking_type.sudo().show_entire_packs = True

    def _create_picking_with_package_level(self, packages):
        picking_form = Form(
            self.env["stock.picking"].with_context(force_detailed_view=True)
        )
        picking_form.partner_id = self.customer
        picking_form.origin = "test"
        picking_form.picking_type_id = self.picking_type
        picking_form.location_id = self.stock_location
        for package in packages:
            with picking_form.package_level_ids_details.new() as move:
                move.package_id = package
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        return picking

    def assert_quant_reserved_qty(self, move_line, qty_func, package=None, lot=None):
        domain = [
            ("location_id", "=", move_line.location_id.id),
            ("product_id", "=", move_line.product_id.id),
        ]
        if package:
            domain.append(("package_id", "=", package.id))
        if lot:
            domain.append(("lot_id", "=", lot.id))
        quant = self.env["stock.quant"].search(domain)
        self.assertEqual(quant.reserved_quantity, qty_func())

    def assert_quant_package_qty(self, location, package, qty_func):
        quant = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("package_id", "=", package.id)]
        )
        self.assertEqual(quant.quantity, qty_func())

    @staticmethod
    def unreachable_func(move_line, message=None):
        raise AssertionError("should not reach this function")

    def test_change_lot_ok(self):
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        source_location = line.location_id
        new_lot = self._create_lot(self.product_a)
        # ensure we have our new package in the same location
        self._update_qty_in_location(source_location, line.product_id, 10, lot=new_lot)
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.lot_replaced_by_lot(initial_lot, new_lot)
            ),
            # failure callback
            self.unreachable_func,
        )
        self.assertRecordValues(line, [{"lot_id": new_lot.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=new_lot)

    def test_change_lot_less_quantity_ok(self):
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        source_location = line.location_id
        new_lot = self._create_lot(self.product_a)
        # ensure we have our new package in the same location
        self._update_qty_in_location(source_location, line.product_id, 8, lot=new_lot)
        expected_message = self.msg_store.lot_replaced_by_lot(initial_lot, new_lot)
        expected_message["body"] += " The quantity to do has changed!"
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
            # failure callback
            self.unreachable_func,
        )
        self.assertRecordValues(line, [{"lot_id": new_lot.id, "reserved_qty": 8}])
        other_line = line.move_id.move_line_ids - line
        self.assertRecordValues(
            other_line, [{"lot_id": initial_lot.id, "reserved_qty": 2}]
        )
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 2, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=new_lot)

    def test_change_lot_zero_quant_error(self):
        """No quant in the location for the scanned lot

        As the user scanned it, it's an inventory error.
        """
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        new_lot = self._create_lot(self.product_a)
        expected_message = self.msg_store.cannot_change_lot_already_picked(new_lot)
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
        )

        self.assertRecordValues(line, [{"lot_id": initial_lot.id, "reserved_qty": 10}])
        # check that reservations have not been updated
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: 0, lot=new_lot)

    def test_change_lot_package_explode_ok(self):
        """Scan a lot on units replacing a package"""
        initial_lot = self._create_lot(self.product_a)
        package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=initial_lot)]
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.lot_id, initial_lot)
        self.assertEqual(line.package_id, package)

        new_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=new_lot)
        expected_message = self.msg_store.lot_replaced_by_lot(initial_lot, new_lot)
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(
            line,
            [
                {
                    "lot_id": new_lot.id,
                    "reserved_qty": 10,
                    "package_id": False,
                    "package_level_id": False,
                }
            ],
        )

        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=new_lot)

    def test_change_lot_reserved_qty_ok(self):
        """Scan a lot already reserved by other lines

        It should unreserve the other line, use the lot for the current line,
        and re-reserve the other move.
        """
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.lot_id, initial_lot)

        new_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=new_lot)
        picking2 = self._create_picking(lines=[(self.product_a, 10)])
        picking2.action_assign()
        line2 = picking2.move_line_ids
        self.assertEqual(line2.lot_id, new_lot)

        expected_message = self.msg_store.lot_replaced_by_lot(initial_lot, new_lot)
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(line, [{"lot_id": new_lot.id, "reserved_qty": 10}])
        # line has been re-created
        line2 = picking2.move_line_ids
        self.assertRecordValues(line2, [{"lot_id": initial_lot.id, "reserved_qty": 10}])

        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=new_lot)
        self.assert_quant_reserved_qty(
            line2, lambda: line2.reserved_qty, lot=initial_lot
        )

    def test_change_lot_reserved_partial_qty_ok(self):
        """Scan a lot already reserved by other lines and can only be reserved
        partially

        It should unreserve the other line, use the lot for the current line,
        and re-reserve the other move. The quantity for the current line must
        be adapted to the available
        """
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.lot_id, initial_lot)

        new_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 8, lot=new_lot)
        picking2 = self._create_picking(lines=[(self.product_a, 8)])
        picking2.action_assign()
        line2 = picking2.move_line_ids
        self.assertEqual(line2.lot_id, new_lot)

        expected_message = self.msg_store.lot_replaced_by_lot(initial_lot, new_lot)
        expected_message["body"] += " The quantity to do has changed!"
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(line, [{"lot_id": new_lot.id, "reserved_qty": 8}])
        other_line = picking.move_line_ids - line
        self.assertRecordValues(
            other_line, [{"lot_id": initial_lot.id, "reserved_qty": 2}]
        )
        # line has been re-created
        line2 = picking2.move_line_ids
        self.assertRecordValues(line2, [{"lot_id": initial_lot.id, "reserved_qty": 8}])

        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=new_lot)
        # both line2 and the line for the 2 remaining will re-reserve the initial lot
        self.assert_quant_reserved_qty(
            other_line,
            lambda: line2.reserved_qty + other_line.reserved_qty,
            lot=initial_lot,
        )

    def test_change_lot_reserved_qty_done_error(self):
        """Scan a lot already reserved by other *picked* lines

        Cannot "steal" lot from picked lines
        """
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.lot_id, initial_lot)

        new_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=new_lot)
        picking2 = self._create_picking(lines=[(self.product_a, 10)])
        picking2.action_assign()
        line2 = picking2.move_line_ids
        self.assertEqual(line2.lot_id, new_lot)
        line2.qty_done = 10.0

        expected_message = self.msg_store.cannot_change_lot_already_picked(new_lot)
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
        )

        # no changes
        self.assertRecordValues(line, [{"lot_id": initial_lot.id, "reserved_qty": 10}])
        self.assertRecordValues(
            line2, [{"lot_id": new_lot.id, "reserved_qty": 10, "qty_done": 10.0}]
        )
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=initial_lot)
        self.assert_quant_reserved_qty(line2, lambda: line2.reserved_qty, lot=new_lot)

    def test_change_lot_different_location_error(self):
        "If the scanned lot is in a different location, we cannot process it"
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        new_lot = self._create_lot(self.product_a)
        # ensure we have our new lot in a different location
        self._update_qty_in_location(self.shelf2, line.product_id, 10, lot=new_lot)
        expected_message = self.msg_store.cannot_change_lot_already_picked(new_lot)
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
        )

        self.assertRecordValues(line, [{"lot_id": initial_lot.id}])
        # check that reservations have not been updated
        self.assert_quant_reserved_qty(line, lambda: line.reserved_qty, lot=initial_lot)
        self.assert_quant_reserved_qty(line, lambda: 0, lot=new_lot)

    def test_change_lot_in_several_packages_error(self):
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=initial_lot)]
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        # create 2 packages for the same new lot in the same location
        new_lot = self._create_lot(self.product_a)
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, new_lot)]
        )
        self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, new_lot)]
        )
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.several_packs_in_location(self.shelf1)
            ),
        )

    def test_change_lot_in_package_ok(self):
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=initial_lot)]
        )
        # ensure we have our new package in the same location
        new_lot = self._create_lot(self.product_a)
        new_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=new_lot)]
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_replaced_by_package(
                    initial_package, new_package
                ),
            ),
            # failure callback
            self.unreachable_func,
        )
        self.assertRecordValues(
            line,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "lot_id": new_lot.id,
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line, lambda: line.reserved_qty, package=new_package
        )

    def test_change_lot_in_package_no_initial_package_ok(self):
        self.product_a.tracking = "lot"
        initial_lot = self._create_lot(self.product_a)
        self._update_qty_in_location(self.shelf1, self.product_a, 10, lot=initial_lot)
        # ensure we have our new package in the same location
        new_lot = self._create_lot(self.product_a)
        new_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=new_lot)]
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.change_package_lot.change_lot(
            line,
            new_lot,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.units_replaced_by_package(new_package)
            ),
            # failure callback
            self.unreachable_func,
        )
        self.assertRecordValues(
            line,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "lot_id": new_lot.id,
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, lot=initial_lot)
        self.assert_quant_reserved_qty(
            line, lambda: line.reserved_qty, package=new_package
        )

    def test_change_pack_different_content_error(self):
        # create the initial package, that will be reserved first
        initial_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, lot=None),
                self.PackageContent(self.product_b, 10, lot=None),
            ],
        )
        picking = self._create_picking_with_package_level(initial_package)
        # create a new package in the same location
        # with a different content
        new_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_b, 8, lot=None)]
        )

        lines = picking.move_line_ids
        # try to use the new package, which doesn't contain our product,
        # cannot be changed
        self.change_package_lot.change_package(
            lines[0],
            new_package,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.package_different_content(new_package)
            ),
        )

    def test_change_pack_multi_content_with_lot(self):
        """Switch package for a line which was part of a multi-products package

        We have a move line which is part of a package with more than one
        product and the other product is moved by another move line.

        We want to pick the goods for product A in a different package. What
        should happen is:

        * the package level is exploded, as we will no longer move the entire
          package
        * the move line for product A should now use the new package, and be
          updated with the lot of the package
        * the move line for the other product should keep the other package, if
          the user want to change the package for the other product too, they
          can do it when they pick it
        """
        (self.product_a + self.product_b).tracking = "lot"
        # create a package with 2 products tracked by lot, stored in shelf1
        # this package is reserved first on the move line
        initial_lot_a = self._create_lot(self.product_a)
        initial_lot_b = self._create_lot(self.product_b)
        initial_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, initial_lot_a),
                self.PackageContent(self.product_b, 10, initial_lot_b),
            ],
        )

        # create and reserve our transfer using the initial package
        picking = self._create_picking_with_package_level(initial_package)

        lines = picking.move_line_ids

        # create a second package with the same content, which will be used
        # as replacement
        new_lot_a = self._create_lot(self.product_a)
        new_lot_b = self._create_lot(self.product_b)
        new_package = self._create_package_in_location(
            self.shelf1,
            [
                self.PackageContent(self.product_a, 10, new_lot_a),
                self.PackageContent(self.product_b, 10, new_lot_b),
            ],
        )
        line1, line2 = lines
        self.change_package_lot.change_package(
            line1,
            new_package,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_replaced_by_package(
                    initial_package, new_package
                ),
            ),
            # failure callback
            self.unreachable_func,
        )
        self.assertRecordValues(
            line1,
            [
                {
                    "package_id": new_package.id,
                    # we are no longer moving an entire package
                    "result_package_id": False,
                    "lot_id": new_lot_a.id,
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(
            line2,
            [
                {
                    "package_id": initial_package.id,
                    # we are no longer moving an entire package
                    "result_package_id": False,
                    "lot_id": initial_lot_b.id,
                    "reserved_qty": 10.0,
                }
            ],
        )
        # check that reservations have been updated
        self.assert_quant_reserved_qty(line1, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line2, lambda: line2.reserved_qty, package=initial_package
        )
        self.assert_quant_reserved_qty(
            line1, lambda: line1.reserved_qty, package=new_package
        )
        self.assert_quant_reserved_qty(line2, lambda: 0, package=new_package)

    def test_change_pack_different_location(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        # put a package in shelf2 in the system, but we assume that in real,
        # the operator put it in shelf1
        new_package = self._create_package_in_location(
            self.shelf2, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.package_id, initial_package)
        # when the operator wants to pick the initial package, in shelf1, the new
        # package is in front of the other so they want to change the package
        self.change_package_lot.change_package(
            line,
            new_package,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_replaced_by_package(
                    initial_package, new_package
                ),
            ),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(
            line, [{"package_id": new_package.id, "result_package_id": new_package.id}]
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        # check that reservations have been updated, the new package is not
        # supposed to be in shelf2 anymore, and we should have no reserved qty
        # for the initial package anymore
        self.assert_quant_package_qty(self.shelf2, new_package, lambda: 0)
        self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line, lambda: line.reserved_qty, package=new_package
        )

    def test_change_pack_different_location_reserved_package(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.package_id, initial_package)

        # put a package in shelf2 in the system, but we assume that in real,
        # the operator put it in shelf1
        new_package = self._create_package_in_location(
            self.shelf2, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking2 = self._create_picking(lines=[(self.product_a, 10)])
        picking2.action_assign()
        line2 = picking2.move_line_ids
        self.assertEqual(line2.package_id, new_package)

        # When the operator wants to pick the initial package, in shelf1, the new
        # package is in front of the other so they want to change the package.
        # The new package was supposed to be in shelf2 but is in fact in
        # shelf1.
        # An inventory must move it in shelf1 before we change the package on the line.
        # Line2 must be unreserved and reserved again.
        self.change_package_lot.change_package(
            line,
            new_package,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_replaced_by_package(
                    initial_package, new_package
                ),
            ),
            # failure callback
            self.unreachable_func,
        )

        # line2 has been re-created
        line2 = picking2.move_line_ids
        self.assertRecordValues(
            line + line2,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "location_id": self.shelf1.id,
                    "reserved_qty": 10.0,
                },
                {
                    "package_id": initial_package.id,
                    "result_package_id": initial_package.id,
                    "location_id": self.shelf1.id,
                    "reserved_qty": 10.0,
                },
            ],
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])
        self.assertRecordValues(
            line2.package_level_id, [{"package_id": initial_package.id}]
        )
        # check that reservations have been updated, the new package is not
        # supposed to be in shelf2 anymore, and we should have no reserved qty
        # for the initial package anymore
        self.assert_quant_package_qty(self.shelf2, new_package, lambda: 0)
        self.assert_quant_reserved_qty(
            line, lambda: line.reserved_qty, package=new_package
        )
        self.assert_quant_reserved_qty(
            line2, lambda: line2.reserved_qty, package=initial_package
        )

    def test_change_pack_different_location_reserved_package_qty_done(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.package_id, initial_package)

        # put a package in shelf2 in the system, but we assume that in real,
        # the operator put it in shelf1
        new_package = self._create_package_in_location(
            self.shelf2, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking2 = self._create_picking(lines=[(self.product_a, 10)])
        picking2.action_assign()
        line2 = picking2.move_line_ids
        self.assertEqual(line2.package_id, new_package)
        line2.qty_done = 10.0

        # The new package was supposed to be in shelf2 but is in fact in shelf1.
        # The package has already been picked in shelf2 (unlikely to happen...
        # still we have to handle it). Forbid to pick.
        expected_message = self.msg_store.package_change_error(
            new_package,
            "Package {} has been partially picked in another location".format(
                new_package.display_name
            ),
        )
        self.change_package_lot.change_package(
            line,
            new_package,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(message, expected_message),
        )

        # line2 has been re-created
        line2 = picking2.move_line_ids
        self.assertRecordValues(
            line + line2,
            [
                {
                    "package_id": initial_package.id,
                    "result_package_id": initial_package.id,
                    "location_id": self.shelf1.id,
                    "reserved_qty": 10.0,
                },
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "location_id": self.shelf2.id,
                    "reserved_qty": 10.0,
                },
            ],
        )
        # no change
        self.assertRecordValues(
            line.package_level_id, [{"package_id": initial_package.id}]
        )
        self.assertRecordValues(
            line2.package_level_id, [{"package_id": new_package.id}]
        )
        self.assert_quant_package_qty(self.shelf2, new_package, lambda: 10.0)
        self.assert_quant_reserved_qty(
            line, lambda: line.reserved_qty, package=initial_package
        )
        self.assert_quant_reserved_qty(
            line2, lambda: line2.reserved_qty, package=new_package
        )

    def test_change_pack_lot_change_pack_less_qty_ok(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 100, lot=None)]
        )

        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids

        self.assertRecordValues(
            line,
            [
                {
                    "package_id": initial_package.id,
                    # since we don't move the entire package (10 out of 100), no
                    # result package
                    "result_package_id": False,
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertFalse(line.package_level_id)

        # ensure we have our new package in the same location
        new_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        self.change_package_lot.change_package(
            line,
            new_package,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_replaced_by_package(
                    initial_package, new_package
                ),
            ),
            # failure callback
            self.unreachable_func,
        )
        self.assertRecordValues(
            line,
            [
                {
                    "package_id": new_package.id,
                    "result_package_id": new_package.id,
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(line.package_level_id, [{"package_id": new_package.id}])

        # check that reservations have been updated
        self.assert_quant_reserved_qty(line, lambda: 0, package=initial_package)
        self.assert_quant_reserved_qty(
            line, lambda: line.reserved_qty, package=new_package
        )

    def test_change_pack_steal_from_other_move_line(self):
        """Exchange pack with another line

        When we scan the package used on another line not picked yet (qty_done
        == 0), we unreserve the other line and use its package. The other line
        is reserved again and should reserve the package used initially on our
        move line.
        """
        # create 2 picking, each with its own package
        package1 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking1 = self._create_picking_with_package_level(package1)
        self.assertEqual(picking1.move_line_ids.package_id, package1)

        package2 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking2 = self._create_picking_with_package_level(package2)
        self.assertEqual(picking2.move_line_ids.package_id, package2)

        line = picking1.move_line_ids

        # We "steal" package2 for the picking1
        self.change_package_lot.change_package(
            line,
            package2,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.package_replaced_by_package(package1, package2)
            ),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(
            picking1.move_line_ids,
            [
                {
                    "package_id": package2.id,
                    "result_package_id": package2.id,
                    "state": "assigned",
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(
            picking2.move_line_ids,
            [
                {
                    "package_id": package1.id,
                    "result_package_id": package1.id,
                    "state": "assigned",
                    "reserved_qty": 10.0,
                }
            ],
        )
        self.assertRecordValues(
            picking1.package_level_ids,
            [{"package_id": package2.id, "state": "assigned"}],
        )
        self.assertRecordValues(
            picking2.package_level_ids,
            [{"package_id": package1.id, "state": "assigned"}],
        )
        # check that reservations have been updated
        self.assert_quant_reserved_qty(
            picking1.move_line_ids,
            lambda: picking1.move_line_ids.reserved_qty,
            package=package2,
        )
        self.assert_quant_reserved_qty(
            picking2.move_line_ids,
            lambda: picking2.move_line_ids.reserved_qty,
            package=package1,
        )

    def test_other_line_with_qty_done(self):
        """Try to exchange pack with other line with qty_done

        When we scan the package used on another line which has been picked
        (qty_done > 0), do not unreserve the other line.
        """
        # create 2 picking, each with its own package
        package1 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking1 = self._create_picking_with_package_level(package1)
        self.assertEqual(picking1.move_line_ids.package_id, package1)

        package2 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking2 = self._create_picking_with_package_level(package2)
        self.assertEqual(picking2.move_line_ids.package_id, package2)

        line1 = picking1.move_line_ids
        line2 = picking2.move_line_ids
        line2.qty_done = 10

        self.change_package_lot.change_package(
            line1,
            package2,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_change_error(
                    package2,
                    "Package {} does not contain available product {},"
                    " cannot replace package.".format(
                        package2.display_name, line1.product_id.display_name
                    ),
                ),
            ),
        )

        # did not change
        self.assertRecordValues(
            picking1.move_line_ids,
            [
                {
                    "package_id": package1.id,
                    "result_package_id": package1.id,
                    "state": "assigned",
                }
            ],
        )
        self.assertRecordValues(
            picking2.move_line_ids,
            [
                {
                    "package_id": package2.id,
                    "result_package_id": package2.id,
                    "state": "assigned",
                }
            ],
        )
        self.assertRecordValues(
            picking1.package_level_ids,
            [{"package_id": package1.id, "state": "assigned"}],
        )
        self.assertRecordValues(
            picking2.package_level_ids,
            [{"package_id": package2.id, "state": "assigned"}],
        )
        # check that reservations have been updated
        self.assert_quant_reserved_qty(
            picking1.move_line_ids,
            lambda: picking1.move_line_ids.reserved_qty,
            package=package1,
        )
        self.assert_quant_reserved_qty(
            picking2.move_line_ids,
            lambda: picking2.move_line_ids.reserved_qty,
            package=package2,
        )

    def test_package_partial(self):
        """Try to exchange pack with a package partially picked

        When we scan the package used on another line which has been picked
        (qty_done > 0), but the new package still has unreserved quantity:

        * the current line is updated for the remaining unreserved quantity
        * a new line is created for the remaining
        * the other already picked line is untouched
        """
        # create 2 picking, each with its own package
        package1 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )
        picking1 = self._create_picking_with_package_level(package1)
        line1 = picking1.move_line_ids
        self.assertEqual(line1.package_id, package1)

        package2 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 10, lot=None)]
        )

        # take partially in package2 (no package level as moving partial
        # package)
        picking2 = self._create_picking(lines=[(self.product_a, 8)])
        picking2.action_assign()
        line2 = picking2.move_line_ids
        self.assertEqual(line2.package_id, package2)

        # this line is picked, should not be changed, but we still have
        # 2 units in package2
        line2.qty_done = line2.reserved_qty

        self.change_package_lot.change_package(
            line1,
            package2,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.package_replaced_by_package(package1, package2)
            ),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(
            line1,
            [
                {
                    "package_id": package2.id,
                    # not moved entirely by this transfer
                    "result_package_id": False,
                    "state": "assigned",
                    # as the remaining was 2 units, the line is
                    # changed to take only 2
                    "reserved_qty": 2.0,
                }
            ],
        )
        self.assertRecordValues(
            # this line should be unchanged
            line2,
            [
                {
                    "package_id": package2.id,
                    # not moved entirely by this transfer
                    "result_package_id": False,
                    "state": "assigned",
                    "reserved_qty": 8.0,
                }
            ],
        )

        # A new line has been created for the quantity the line1
        # couldn't take in package2. It will take the first goods
        # available, which happen to be package1 (which was unreserved
        # when we changed the package of line1).
        remaining_line = picking1.move_line_ids - line1
        self.assertRecordValues(
            remaining_line,
            [
                {
                    "package_id": package1.id,
                    # not moved entirely by this transfer
                    "result_package_id": False,
                    "state": "assigned",
                    # remaining qty for the 1st move
                    "reserved_qty": 8.0,
                }
            ],
        )

        # the package1 must have only 8 reserved, for the remaining
        # of the line
        self.assertEqual(package1.quant_ids.reserved_quantity, 8)
        self.assertEqual(package2.quant_ids.reserved_quantity, 10)

        # no package is moved entirely at once
        self.assertFalse(picking1.package_level_ids)
        self.assertFalse(picking2.package_level_ids)

    def test_package_2_lines_1_move(self):
        """Keep picked move line if we have 2 lines on a move

        Create a situation where we have 2 move lines on a move, with different
        packages, 1 one of them is already picked (qty_done > 0), we change the
        package on the second one: the first one must not be changed.
        """
        package1 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 4, lot=None)]
        )
        package2 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 8, lot=None)]
        )

        # take partially in package2 (no package level as moving partial
        # package)
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        move = picking.move_ids
        line1, line2 = move.move_line_ids
        self.assertEqual(line1.package_id, package1)
        self.assertEqual(line2.package_id, package2)

        # package to switch to
        package3 = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 8, lot=None)]
        )

        # this line is picked and must not be changed
        line1.qty_done = line1.reserved_qty

        # as we change for package2, the line should get only the remaining
        # part of the package

        self.change_package_lot.change_package(
            line2,
            package3,
            # success callback
            lambda move_line, message=None: self.assertEqual(
                message, self.msg_store.package_replaced_by_package(package2, package3)
            ),
            # failure callback
            self.unreachable_func,
        )

        self.assertRecordValues(
            line1 | line2,
            [
                {
                    "package_id": package1.id,
                    "state": "assigned",
                    "reserved_qty": 4.0,
                    "qty_done": 4.0,
                },
                {
                    "package_id": package3.id,
                    "state": "assigned",
                    "reserved_qty": 6.0,
                    "qty_done": 0.0,
                },
            ],
        )

        # package1 is moved entirely
        self.assertTrue(line1.package_level_id)
        # package2 is not moved entirely
        self.assertFalse(line2.package_level_id)

        # the package1 must have only 8 reserved, for the remaining
        # of the line
        self.assertEqual(package1.quant_ids.reserved_quantity, 4)
        self.assertEqual(package2.quant_ids.reserved_quantity, 0)
        self.assertEqual(package3.quant_ids.reserved_quantity, 6)

    def test_change_pack_same(self):
        initial_package = self._create_package_in_location(
            self.shelf1, [self.PackageContent(self.product_a, 100, lot=None)]
        )
        picking = self._create_picking(lines=[(self.product_a, 10)])
        picking.action_assign()
        line = picking.move_line_ids
        self.assertEqual(line.package_id, initial_package)
        self.change_package_lot.change_package(
            line,
            initial_package,
            # success callback
            self.unreachable_func,
            # failure callback
            lambda move_line, message=None: self.assertEqual(
                message,
                self.msg_store.package_change_error_same_package(initial_package),
            ),
        )
