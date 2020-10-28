# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseRelease(PromiseReleaseCommonCase):
    def _prev_picking(self, picking):
        return picking.move_lines.move_orig_ids.picking_id

    def _out_picking(self, pickings):
        return pickings.filtered(lambda r: r.picking_type_code == "outgoing")

    def _deliver(self, picking):
        picking.action_assign()
        for line in picking.mapped("move_lines.move_line_ids"):
            line.qty_done = line.product_qty
        picking.action_done()

    def test_qty_ctx(self):
        move = self.env["stock.move"].create(
            {
                "name": "testing ctx",
                "product_id": self.product1.id,
                "product_uom_qty": 1,
                "product_uom": self.uom_unit.id,
                "warehouse_id": self.wh.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customer.id,
            }
        )
        ctx = move._order_available_to_promise_qty_ctx()
        self.assertEqual(ctx["location"], self.wh.lot_stock_id.id)

    def test_horizon_date(self):
        move = self.env["stock.move"].create(
            {
                "name": "testing ctx",
                "product_id": self.product1.id,
                "product_uom_qty": 1,
                "product_uom": self.uom_unit.id,
                "warehouse_id": self.wh.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customer.id,
            }
        )
        self.env.company.stock_reservation_horizon = 0
        self.assertEqual(move._promise_reservation_horizon_date(), None)
        # set 15 days
        self.env.company.stock_reservation_horizon = 15
        from_date = datetime.now().replace(hour=23, minute=59, second=59)
        to_date = from_date + relativedelta(days=15)
        self.assertEqual(
            # skip millisec
            move._promise_reservation_horizon_date().timetuple()[:6],
            to_date.timetuple()[:6],
        )
        # lower to 5
        self.env.company.stock_reservation_horizon = 5
        to_date = from_date + relativedelta(days=5)
        self.assertEqual(
            # skip millisec
            move._promise_reservation_horizon_date().timetuple()[:6],
            to_date.timetuple()[:6],
        )

    def _create_pickings(self):
        picking = self._out_picking(
            self._create_picking_chain(
                self.wh, [(self.product1, 5)], date=datetime(2019, 9, 2, 16, 0)
            )
        )
        picking2 = self._out_picking(
            self._create_picking_chain(
                self.wh, [(self.product1, 3)], date=datetime(2019, 9, 3, 16, 1)
            )
        )
        # we'll assign this one in the test, should deduct pick 1 and 2
        picking3 = self._out_picking(
            self._create_picking_chain(
                self.wh, [(self.product1, 20)], date=datetime(2019, 9, 4, 16, 0)
            )
        )
        # this one should be ignored when we'll assign pick 3 as it has
        # a later date
        picking4 = self._out_picking(
            self._create_picking_chain(
                self.wh, [(self.product1, 20)], date=datetime(2019, 9, 5, 16, 1)
            )
        )
        # another one to test priority ordering
        picking5 = self._out_picking(
            self._create_picking_chain(
                self.wh, [(self.product1, 15)], date=datetime(2019, 9, 6, 16, 1)
            )
        )
        for pick in (picking, picking2, picking3, picking4, picking5):
            self.assertEqual(pick.state, "waiting")
            self.assertEqual(pick.move_lines.reserved_availability, 0.0)
        return picking, picking2, picking3, picking4, picking5

    def test_ordered_available_to_promise_value(self):
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})
        picking, picking2, picking3, picking4, picking5 = self._create_pickings()

        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)

        self.assertEqual(picking.move_lines._ordered_available_to_promise(), 5)
        self.assertEqual(picking2.move_lines._ordered_available_to_promise(), 3)
        self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 12)
        self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking5.move_lines._ordered_available_to_promise(), 0)

        self.env.company.stock_reservation_horizon = 1
        with freeze_time("2019-09-03"):
            # set expected date for picking moves far in the future
            picking_orig_date_expected = picking.move_lines.date_expected
            picking.move_lines.write({"date_expected": "2019-09-10"})
            # its quantity won't be counted ib previously reserved
            # and we get 3 more on the next one
            self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 17)
            # do the same for picking 2
            picking2_orig_date_expected = picking2.move_lines.date_expected
            picking2.move_lines.write({"date_expected": "2019-09-10"})
            # its quantity won't be counted ib previously reserved
            # and we get 3 more on the next one
            self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 20)
            self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 0)
            picking3_orig_date_expected = picking3.move_lines.date_expected
            picking3.move_lines.write({"date_expected": "2019-09-10"})
            self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 20)
            # set a higher priority for picking 5
            # (restoring previous date_expected values for other pickings before)
            picking.move_lines.date_expected = picking_orig_date_expected
            picking2.move_lines.date_expected = picking2_orig_date_expected
            picking3.move_lines.date_expected = picking3_orig_date_expected
            picking5.move_lines.write(
                {"date_expected": "2019-09-01", "date_priority": "2019-09-01"}
            )
            self.assertEqual(picking5.move_lines._ordered_available_to_promise(), 15)
            self.assertEqual(picking.move_lines._ordered_available_to_promise(), 5)
            self.assertEqual(picking2.move_lines._ordered_available_to_promise(), 0)

        # move the horizon fwd
        self.env.company.stock_reservation_horizon = 10
        with freeze_time("2019-09-03"):
            # last picking won't have available qty again
            self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 0)

    def test_ordered_available_to_promise_value_by_priority(self):
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})
        picking, picking2, picking3, picking4, picking5 = self._create_pickings()

        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)

        self.assertEqual(picking.move_lines._ordered_available_to_promise(), 5)
        self.assertEqual(picking2.move_lines._ordered_available_to_promise(), 3)
        self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 12)
        self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking5.move_lines._ordered_available_to_promise(), 0)

        # Set a higher priority on the picking4 (need of 20 units)
        picking4_orig_priority = picking4.priority
        picking4.priority = "2"
        self.assertEqual(picking.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking2.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 20)
        self.assertEqual(picking5.move_lines._ordered_available_to_promise(), 0)

        # Set a higher priority on the picking 3 (need of 20 units)
        picking3_orig_priority = picking3.priority
        picking3.priority = "3"
        self.assertEqual(picking.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking2.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 20)
        self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking5.move_lines._ordered_available_to_promise(), 0)

        # Set a higher priority on the picking 5 (need of 15 units)
        picking3.priority = picking3_orig_priority
        picking4.priority = picking4_orig_priority
        picking5.priority = "2"
        self.assertEqual(picking.move_lines._ordered_available_to_promise(), 5)
        self.assertEqual(picking2.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking3.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking4.move_lines._ordered_available_to_promise(), 0)
        self.assertEqual(picking5.move_lines._ordered_available_to_promise(), 15)

    def test_normal_chain(self):
        # usual scenario, without using the option to defer the pull
        pickings = self._create_picking_chain(self.wh, [(self.product1, 5)])
        self.assertEqual(len(pickings), 2, "expect stock->out + out->customer")
        self.assertRecordValues(
            pickings.sorted("id"),
            [
                {
                    "location_id": self.wh.lot_stock_id.id,
                    "location_dest_id": self.wh.wh_output_stock_loc_id.id,
                },
                {
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                },
            ],
        )

    def test_defer_creation(self):
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        self._update_qty_in_location(self.loc_bin1, self.product1, 20.0)
        pickings = self._create_picking_chain(self.wh, [(self.product1, 5)])

        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )

        cust_picking.move_lines.release_available_to_promise()
        out_picking = self._pickings_in_group(pickings.group_id) - cust_picking

        self.assertRecordValues(
            out_picking,
            [
                {
                    "state": "assigned",
                    "location_id": self.wh.lot_stock_id.id,
                    "location_dest_id": self.wh.wh_output_stock_loc_id.id,
                }
            ],
        )

    def test_defer_creation_move_type_one(self):
        """Deliver all products at once"""
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        self._update_qty_in_location(self.loc_bin1, self.product1, 5.0)
        pickings = self._create_picking_chain(
            self.wh, [(self.product1, 10.0)], move_type="one"
        )
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )

        cust_picking.move_lines.release_available_to_promise()
        # no chain picking should have been created because we would have a
        # partial and the move delivery type is "one"
        out_picking = self._pickings_in_group(pickings.group_id) - cust_picking
        self.assertFalse(out_picking)

        self._update_qty_in_location(self.loc_bin1, self.product1, 10.0)
        # now, we have enough, the picking is created
        cust_picking.move_lines.release_available_to_promise()
        out_picking = self._pickings_in_group(pickings.group_id) - cust_picking
        self.assertRecordValues(
            out_picking,
            [
                {
                    "state": "assigned",
                    "location_id": self.wh.lot_stock_id.id,
                    "location_dest_id": self.wh.wh_output_stock_loc_id.id,
                }
            ],
        )

    def test_defer_creation_backorder(self):
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        self._update_qty_in_location(self.loc_bin1, self.product1, 7.0)

        pickings = self._create_picking_chain(self.wh, [(self.product1, 20)])
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                    "printed": False,
                }
            ],
        )

        cust_picking.release_available_to_promise()
        split_cust_picking = cust_picking.backorder_ids
        self.assertEqual(len(split_cust_picking), 1)
        out_picking = (
            self._pickings_in_group(pickings.group_id)
            - cust_picking
            - split_cust_picking
        )

        # the complete one is assigned and placed into stock output
        self.assertRecordValues(
            out_picking,
            [
                {
                    "state": "assigned",
                    "location_id": self.wh.lot_stock_id.id,
                    "location_dest_id": self.wh.wh_output_stock_loc_id.id,
                    "printed": True,
                }
            ],
        )
        # the released customer picking is set to "printed"
        self.assertRecordValues(cust_picking, [{"printed": True}])
        # the split once stays in the original location
        self.assertRecordValues(
            split_cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                    "printed": False,
                }
            ],
        )

        self.assertRecordValues(out_picking.move_lines, [{"product_qty": 7.0}])
        self.assertRecordValues(split_cust_picking.move_lines, [{"product_qty": 13.0}])

        # let's deliver what we can
        self._deliver(out_picking)
        self.assertRecordValues(out_picking, [{"state": "done"}])

        self.assertRecordValues(cust_picking, [{"state": "assigned"}])
        self.assertRecordValues(
            cust_picking.move_lines,
            [
                {
                    "state": "assigned",
                    "product_qty": 7.0,
                    "reserved_availability": 7.0,
                    "procure_method": "make_to_order",
                }
            ],
        )
        self.assertRecordValues(split_cust_picking, [{"state": "waiting"}])
        self.assertRecordValues(
            split_cust_picking.move_lines,
            [
                {
                    "state": "waiting",
                    "product_qty": 13.0,
                    "reserved_availability": 0.0,
                    "procure_method": "make_to_order",
                }
            ],
        )

        self._deliver(cust_picking)
        self.assertRecordValues(cust_picking, [{"state": "done"}])

        cust_backorder = (
            self._pickings_in_group(cust_picking.group_id) - cust_picking - out_picking
        )
        self.assertEqual(len(cust_backorder), 1)

        # nothing happen, no stock
        self.assertEqual(len(self._pickings_in_group(cust_picking.group_id)), 3)
        cust_backorder.release_available_to_promise()
        self.assertEqual(len(self._pickings_in_group(cust_picking.group_id)), 3)

        # We add stock, so now the release must create the next
        # chained move
        self._update_qty_in_location(self.loc_bin1, self.product1, 30)
        cust_backorder.release_available_to_promise()
        out_backorder = (
            self._pickings_in_group(cust_picking.group_id)
            - cust_backorder
            - cust_picking
            - out_picking
        )
        self.assertRecordValues(
            out_backorder.move_lines,
            [
                {
                    "state": "assigned",
                    "product_qty": 13.0,
                    "reserved_availability": 13.0,
                    "procure_method": "make_to_stock",
                    "location_id": self.wh.lot_stock_id.id,
                    "location_dest_id": self.wh.wh_output_stock_loc_id.id,
                }
            ],
        )

    def test_defer_multi_move_unreleased_in_backorder(self):
        """Unreleased moves are put in a backorder"""
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        self._update_qty_in_location(self.loc_bin1, self.product1, 10.0)
        self._update_qty_in_location(self.loc_bin1, self.product2, 10.0)

        pickings = self._create_picking_chain(
            self.wh,
            [
                (self.product1, 20),
                (self.product2, 10),
                (self.product3, 20),
                (self.product4, 10),
            ],
        )
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )
        cust_picking = pickings
        cust_picking.release_available_to_promise()

        backorder = cust_picking.backorder_ids
        self.assertRecordValues(
            backorder,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )

        self.assertRecordValues(
            backorder.move_lines,
            [
                # remaining 10 on product 1 because it was partially available
                {"product_qty": 10.0, "product_id": self.product1.id},
                # these 2 moves were not released, so they are moved to a
                # backorder
                {"product_qty": 20.0, "product_id": self.product3.id},
                {"product_qty": 10.0, "product_id": self.product4.id},
            ],
        )

        out_picking = (
            self._pickings_in_group(pickings.group_id) - cust_picking - backorder
        )

        self.assertRecordValues(
            out_picking,
            [
                {
                    "state": "assigned",
                    "location_id": self.wh.lot_stock_id.id,
                    "location_dest_id": self.wh.wh_output_stock_loc_id.id,
                }
            ],
        )

        self.assertRecordValues(
            out_picking.move_lines,
            [
                {"product_qty": 10.0, "product_id": self.product1.id},
                {"product_qty": 10.0, "product_id": self.product2.id},
            ],
        )

    def test_defer_creation_uom(self):
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})

        self._update_qty_in_location(self.loc_bin1, self.product1, 12.0)
        uom_dozen = self.env.ref("uom.product_uom_dozen")
        pickings = self._create_picking_chain(
            self.wh,
            # means 24 products
            [(self.product1, 2, uom_dozen)],
        )
        self.assertEqual(len(pickings), 1, "expect only the last out->customer")
        cust_picking = pickings
        self.assertRecordValues(
            cust_picking,
            [
                {
                    "state": "waiting",
                    "location_id": self.wh.wh_output_stock_loc_id.id,
                    "location_dest_id": self.loc_customer.id,
                }
            ],
        )
        self.assertRecordValues(
            cust_picking.move_lines,
            [
                {
                    "state": "waiting",
                    "product_uom": uom_dozen.id,
                    "product_qty": 24.0,
                    "product_uom_qty": 2.0,
                    "ordered_available_to_promise": 12.0,
                }
            ],
        )

        cust_picking.move_lines.release_available_to_promise()
        split_cust_picking = cust_picking.backorder_ids
        self.assertEqual(len(split_cust_picking), 1)
        out_picking = (
            self._pickings_in_group(pickings.group_id)
            - cust_picking
            - split_cust_picking
        )

        self.assertRecordValues(
            out_picking.move_lines,
            [
                {
                    "state": "assigned",
                    "product_qty": 12.0,
                    "reserved_availability": 1.0,
                    "product_uom_qty": 1.0,
                }
            ],
        )
        self.assertRecordValues(
            split_cust_picking.move_lines,
            [
                {
                    "state": "waiting",
                    "product_qty": 12.0,
                    "reserved_availability": 0.0,
                    "product_uom_qty": 1.0,
                }
            ],
        )

    def test_mto_picking(self):
        self.wh.delivery_route_id.write({"available_to_promise_defer_pull": True})
        # TODO a MTO picking should work normally

    # TODO: test w/ multiple orders by priority
