# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingStockIssue(ClusterPickingCommonCase):
    """Tests covering the /stock_issue endpoint
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # quants already existing are from demo data
        loc_ids = (cls.stock_location.id, cls.shelf1.id, cls.shelf2.id)
        cls.env["stock.quant"].sudo().search([("location_id", "in", loc_ids)]).unlink()
        cls.batch = cls._create_picking_batch(
            [
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
                [cls.BatchProduct(product=cls.product_a, quantity=5)],
                [cls.BatchProduct(product=cls.product_a, quantity=20)],
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
                [cls.BatchProduct(product=cls.product_a, quantity=7)],
            ]
        )

        cls.moves = cls.batch.picking_ids.move_lines.sorted("id")
        cls.move1, cls.move2, cls.move3, cls.move4, cls.move5 = cls.moves
        cls.batch_other = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=30)]]
        )
        cls.dest_package = cls.env["stock.quant.package"].create({})

    def _stock_issue(self, line, next_line_func=None):
        batch = line.picking_id.batch_id
        response = self.service.dispatch(
            "stock_issue",
            params={"picking_batch_id": batch.id, "move_line_id": line.id},
        )
        # use a function/lambda to delay the read of the next line,
        # when calling _stock_issue(), the move_line may not exist and
        # be created during the call to the stock_issue service
        if next_line_func:
            self.assert_response(
                response,
                next_state="start_line",
                data=self._line_data(next_line_func()),
            )
        else:
            self.assert_response(
                response,
                next_state="unload_all",
                data=self._data_for_batch(self.batch, self.packing_location),
            )
        return response

    def assert_location_qty_and_reserved(
        self, location, expected_reserved_qty, lot=None
    ):
        quant_domain = [("location_id", "=", location.id)]
        if lot:
            quant_domain += [("lot_id", "=", lot.id)]
        location_quants = self.env["stock.quant"].search(quant_domain)
        self.assertEqual(sum(location_quants.mapped("quantity")), expected_reserved_qty)
        self.assertEqual(
            sum(location_quants.mapped("reserved_quantity")), expected_reserved_qty
        )

    def assert_stock_issue_inventories(
        self, issue_picking, location, product, remaining_qty, lot=None
    ):
        inventories = self.env["stock.inventory"].search([], order="id desc", limit=2)
        product_desc = product.name
        if lot:
            product_desc = "{} - Lot: {}".format(product_desc, lot.name)
        self.assertRecordValues(
            inventories,
            [
                {
                    # this one changed the quantity in the location to
                    # the quantity of the quant checked above
                    "state": "done",
                    "name": "{picking.name} stock correction in"
                    " location {location.name} for {product_desc}".format(
                        picking=issue_picking,
                        location=location,
                        product_desc=product_desc,
                    ),
                },
                {
                    # this one is draft and empty, has to be done by a user
                    "state": "draft",
                    "name": "Control stock issue in location {} for {}".format(
                        location.name, product_desc
                    ),
                },
            ],
        )
        self.assertRecordValues(
            inventories[0].line_ids,
            [
                {
                    "product_id": product.id,
                    "location_id": location.id,
                    "product_qty": remaining_qty,
                    "package_id": False,
                    "prod_lot_id": lot.id if lot else False,
                }
            ],
        )

    def test_stock_issue_with_other_batch(self):
        self._update_qty_in_location(self.shelf1, self.product_a, 25)
        # The other batch will reserve 25 in shelf 1, now empty
        self.batch_other.picking_ids.action_assign()

        self._update_qty_in_location(self.shelf2, self.product_a, 100)
        # and then, the other batch reserves 5 in shelf 2.
        # We'll want to check that even if on our batch we have a stock issue,
        # we never change anything in the batch of another operator.
        self._simulate_batch_selected(self.batch_other, fill_stock=False)
        self.assertEqual(
            set(self.batch_other.picking_ids.mapped("state")), {"assigned"}
        )

        # At this point, we have a remaining quantity of 0 in shelf1
        # and 95 in shelf2.

        # all the moves of our batch should be reserved as we have enough
        # stock
        self._simulate_batch_selected(self.batch, fill_stock=False)
        self.assertEqual(set(self.batch.picking_ids.mapped("state")), {"assigned"})

        # the operator could pick the 2 first lines of the batch
        self._set_dest_package_and_done(self.move1.move_line_ids, self.dest_package)
        self._set_dest_package_and_done(self.move2.move_line_ids, self.dest_package)

        # on the third move, the operator can't pick anymore in shelf1
        # because there is nothing inside, they declare a stock issue
        self._stock_issue(self.move3.move_line_ids)

        self.assertRecordValues(
            self.moves,
            [
                {"state": "assigned"},
                {"state": "assigned"},
                {"state": "confirmed"},
                {"state": "confirmed"},
                {"state": "confirmed"},
            ],
        )
        expected_reserved_qty = (
            self.move1.product_uom_qty
            + self.move2.product_uom_qty
            + sum(
                self.batch_other.picking_ids.move_line_ids.filtered(
                    lambda l: l.location_id == self.shelf2
                ).mapped("product_uom_qty")
            )
        )
        # we should have a quant with 20 quantity and 20 reserved
        # (5 for the other batch and 15 qty_done in this batch)
        self.assert_location_qty_and_reserved(self.shelf2, expected_reserved_qty)
        self.assert_stock_issue_inventories(
            self.move3.picking_id,
            self.shelf2,
            self.move3.product_id,
            expected_reserved_qty,
        )

    def test_stock_issue_several_move_lines(self):
        self._update_qty_in_location(self.shelf1, self.product_a, 20)
        # ensure these moves are reserved in shelf1
        self.move1._action_assign()
        self.move2._action_assign()

        self._update_qty_in_location(self.shelf2, self.product_a, 100)
        # reserve move3 first to ensure this one is reserved in both
        # shelf1 and shelf2
        self.move3._action_assign()

        # all the remaining moves will be reserved in shelf2
        self._simulate_batch_selected(self.batch, fill_stock=False)
        self.assertEqual(set(self.batch.picking_ids.mapped("state")), {"assigned"})
        # The moves of our batch are reserved as:
        self.assertEqual(self.move1.move_line_ids.location_id, self.shelf1)
        self.assertEqual(self.move2.move_line_ids.location_id, self.shelf1)
        self.assertEqual(
            self.move3.move_line_ids.mapped("location_id"), self.shelf1 | self.shelf2
        )
        self.assertEqual(self.move4.move_line_ids.location_id, self.shelf2)
        self.assertEqual(self.move5.move_line_ids.location_id, self.shelf2)

        line_shelf1 = self.move3.move_line_ids.filtered(
            lambda l: l.location_id == self.shelf1
        )
        line_shelf2 = self.move3.move_line_ids.filtered(
            lambda l: l.location_id == self.shelf2
        )

        # pick the first 2 moves
        self._set_dest_package_and_done(self.move1.move_line_ids, self.dest_package)
        self._set_dest_package_and_done(self.move2.move_line_ids, self.dest_package)
        # the operator could pick the first part of move3 in shelf1
        self._set_dest_package_and_done(line_shelf1, self.dest_package)

        # on the third move, the operator can't pick anymore in shelf1
        # because there is nothing inside, they declare a stock issue
        self._stock_issue(line_shelf2)

        self.assertRecordValues(
            self.moves,
            [
                # move 1 and 2 aren't touched: they are in another location
                {"state": "assigned"},
                {"state": "assigned"},
                {"state": "partially_available"},
                {"state": "confirmed"},
                {"state": "confirmed"},
            ],
        )
        self.assertRecordValues(
            # check that the other move line of the move was not altered
            line_shelf1,
            [
                {
                    "location_id": self.shelf1.id,
                    "qty_done": 5.0,
                    "result_package_id": self.dest_package.id,
                }
            ],
        )
        self.assertFalse(line_shelf2.exists())
        # the quantity in shelf1 should be the original one since we didn't have
        # a stock issue here
        self.assert_location_qty_and_reserved(self.shelf1, 20)
        # since we declared the stock issue without picking anything, its
        # quantity should be zero
        self.assert_location_qty_and_reserved(self.shelf2, 0)
        self.assert_stock_issue_inventories(
            self.move3.picking_id, self.shelf2, self.move3.product_id, 0
        )

    def test_stock_issue_lot(self):
        lot_a = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        lot_b = self.env["stock.production.lot"].create(
            {"product_id": self.product_a.id, "company_id": self.env.company.id}
        )
        self._update_qty_in_location(
            self.shelf2,
            self.product_a,
            self.move1.product_uom_qty + self.move5.product_uom_qty,
            lot=lot_a,
        )
        # ensure that move 1 and 5 take lot_a (10 + 7 units), so all of them
        self.move1._action_assign()
        self.move5._action_assign()
        # add stock for the rest of the moves
        self._update_qty_in_location(self.shelf2, self.product_a, 100, lot=lot_b)
        # reserve the remaining moves
        self._simulate_batch_selected(self.batch, fill_stock=False)
        self.assertEqual(set(self.batch.picking_ids.mapped("state")), {"assigned"})

        # the operator could pick the 3 first lines of the batch
        # move move1 with lot a
        self._set_dest_package_and_done(self.move1.move_line_ids, self.dest_package)
        # move move2 with lot b
        self._set_dest_package_and_done(self.move2.move_line_ids, self.dest_package)

        # on the third move, the operator can't pick anymore in the location,
        # because there is nothing inside, they declare a stock issue
        self._stock_issue(
            self.move3.move_line_ids, next_line_func=lambda: self.move5.move_line_ids
        )

        self.assertRecordValues(
            self.moves,
            [
                # still reserved because using lot a
                {"state": "assigned"},
                # still reserved because qty_done > 0
                {"state": "assigned"},
                # unreserved by the stock issue
                {"state": "confirmed"},
                # collaterally unreserved by the stock issue (same lot as the
                # stock issue)
                {"state": "confirmed"},
                # still reserved because using lot a
                {"state": "assigned"},
            ],
        )
        # check the qty including lot a and lot b
        total_reserved_qty = (
            self.move1.product_uom_qty
            + self.move2.product_uom_qty
            + self.move5.product_uom_qty
        )
        self.assert_location_qty_and_reserved(self.shelf2, total_reserved_qty)
        # this is the only product reserved for lot_b
        expected_reserved_qty = self.move2.product_uom_qty
        self.assert_location_qty_and_reserved(
            self.shelf2, expected_reserved_qty, lot=lot_b
        )
        self.assert_stock_issue_inventories(
            self.move3.picking_id,
            self.shelf2,
            self.move3.product_id,
            expected_reserved_qty,
            lot=lot_b,
        )

    def test_stock_issue_reserve_elsewhere(self):
        self._update_qty_in_location(self.shelf1, self.product_a, 100)
        self._simulate_batch_selected(self.batch, fill_stock=False)
        # now, everything is reserved in shelf1 as we had enough stock
        self.assertEqual(set(self.batch.picking_ids.mapped("state")), {"assigned"})

        # put stock in shelf2, so we can test the outcome: goods should be
        # reserved in shelf2 after a stock issue
        self._update_qty_in_location(self.shelf2, self.product_a, 100)

        # the operator picks the first line
        self._set_dest_package_and_done(self.move1.move_line_ids, self.dest_package)

        # and has a stock issue on the second line
        # because there is nothing inside, they declare a stock issue
        self._stock_issue(
            self.move2.move_line_ids, next_line_func=lambda: self.move2.move_line_ids
        )

        # the inventory should have been done for shelf1, and all the remaining
        # moves after move1 (already picked) should have been reserved in
        # shelf2
        self.assertEqual(set(self.batch.picking_ids.mapped("state")), {"assigned"})
        self.assertEqual(self.move1.move_line_ids.location_id, self.shelf1)
        # all the following moves have been reserved in shelf2 as we still have
        # stock there
        self.assertEqual(
            (self.move2 | self.move3 | self.move4 | self.move5).mapped(
                "move_line_ids.location_id"
            ),
            self.shelf2,
        )

    def test_stock_issue_similar_move_with_picked_line(self):
        """Stock issue on the remaining of a line on partial move

        We have a move with 10 units.
        2 are reserved in a package. The remaining in another package.
        We pick 1 of the first package and put it in a bin.
        A new move line of 1 is created to pick in the first package: we
        declare a stock out on it.
        The first move line must be untouched, the second line for the remaining
        should pick one more item in the other package.
        """
        package1 = self.env["stock.quant.package"].create({"name": "PACKAGE_1"})
        package2 = self.env["stock.quant.package"].create({"name": "PACKAGE_2"})
        self._update_qty_in_location(self.shelf1, self.product_a, 2, package=package1)
        self._update_qty_in_location(self.shelf1, self.product_a, 200, package=package2)
        self.move1._action_assign()
        self.move2._action_assign()
        self.move3._action_assign()
        self._simulate_batch_selected(self.batch, fill_stock=False)
        self.assertEqual(set(self.batch.picking_ids.mapped("state")), {"assigned"})

        pick_line1, pick_line2 = self.move1.move_line_ids
        new_line, __ = pick_line1._split_qty_to_be_done(1)
        self._set_dest_package_and_done(pick_line1, self.dest_package)

        self.assertEqual(pick_line1.product_qty, 1.0)
        self.assertEqual(new_line.product_qty, 1.0)
        self.assertEqual(pick_line2.product_qty, 8.0)
        # on the third move, the operator can't pick anymore in shelf1
        # because there is nothing inside, they declare a stock issue
        self._stock_issue(new_line, next_line_func=lambda: pick_line2)

        self.assertRecordValues(
            # check that the first move line of the move was not altered
            pick_line1,
            [
                {
                    "location_id": self.shelf1.id,
                    "qty_done": 1.0,
                    "result_package_id": self.dest_package.id,
                }
            ],
        )
        # the line on which we declared stock out does not exists
        self.assertFalse(new_line.exists())
        # the second line to pick has been raised to 9 instead of 8
        # initially, to compensate the stock out
        self.assertEqual(pick_line2.product_qty, 9.0)

        # quant with stock out has been updated
        self.assertEqual(package1.quant_ids.quantity, 1.0)
