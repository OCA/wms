from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingStockIssue(ClusterPickingCommonCase):
    """Tests covering the /stock_issue endpoint
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # quants already existing are from demo data
        loc_ids = (cls.stock_location.id, cls.shelf1.id, cls.shelf2.id)
        cls.env["stock.quant"].search([("location_id", "in", loc_ids)]).unlink()
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

    def _stock_issue(self, line, next_line=None):
        response = self.service.dispatch(
            "stock_issue", params={"move_line_id": line.id}
        )
        if next_line:
            self.assert_response(
                response, next_state="start_line", data=self._line_data(next_line)
            )
        else:
            self.assert_response(
                response,
                next_state="unload_all",
                data={
                    "id": self.batch.id,
                    "location_dest": {
                        "id": self.packing_location.id,
                        "name": self.packing_location.name,
                    },
                    "name": self.batch.name,
                },
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
        self._stock_issue(self.move3.move_line_ids, next_line=self.move5.move_line_ids)

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
