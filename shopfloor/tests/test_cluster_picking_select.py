from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingSelectionCase(ClusterPickingCommonCase):
    """Tests covering the selection of picking batches

    Endpoints:

    * /cluster_picking/find_batch
    * /cluster_picking/list_batch
    * /cluster_picking/select
    * /cluster_picking/unassign

    These endpoints interact with a list of picking batches.
    The other endpoints that interact with a single batch (after selection)
    are handled in other classes.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # drop base demo data and create our own batches to work with
        cls.env["stock.picking.batch"].search([]).unlink()
        cls.batch1 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=3)]]
        )
        cls.batch2 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=3)]]
        )
        cls.batch3 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=3)]]
        )
        cls.batch4 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=3)]]
        )

    def _add_stock_and_assign_pickings_for_batches(self, batches):
        pickings = batches.mapped("picking_ids")
        self._fill_stock_for_moves(pickings.mapped("move_lines"))
        pickings.action_assign()

    def test_find_batch_in_progress_current_user(self):
        """Find an in-progress batch assigned to the current user"""
        # Simulate the client asking a batch by clicking on "get work"
        self._add_stock_and_assign_pickings_for_batches(
            self.batch1 | self.batch2 | self.batch3
        )
        self.batch3.user_id = self.env.uid
        self.batch3.confirm_picking()  # set to in progress
        response = self.service.dispatch("find_batch")

        # we expect to find batch 3 as it's assigned to the current
        # user and in progress (first priority)
        self.assert_response(
            response,
            next_state="confirm_start",
            data={
                "id": self.batch3.id,
                "name": self.batch3.name,
                "pickings": [
                    {
                        "id": self.batch3.picking_ids.id,
                        "name": self.batch3.picking_ids.name,
                        "move_line_count": len(self.batch3.picking_ids.move_line_ids),
                        "origin": self.batch3.picking_ids.origin,
                        # quantity of products (3) * weight of product (2)
                        "weight": 6.0,
                        "partner": {
                            "id": self.batch3.picking_ids.partner_id.id,
                            "name": self.batch3.picking_ids.partner_id.name,
                        },
                    }
                ],
            },
        )

    def test_find_batch_assigned(self):
        """Find a draft batch assigned to the current user"""
        # batches must have all their pickings available to be selected
        self._add_stock_and_assign_pickings_for_batches(
            self.batch1 | self.batch2 | self.batch3
        )
        # batch2 in draft but assigned to the current user should be
        # selected before the others
        self.batch2.user_id = self.env.uid
        response = self.service.dispatch("find_batch")

        # The endpoint starts the batch
        self.assertEqual(self.batch2.state, "in_progress")

        # we expect to find batch 2 as it's assigned to the current user
        self.assert_response(
            response,
            next_state="confirm_start",
            data={
                "id": self.batch2.id,
                "name": self.batch2.name,
                "pickings": [
                    {
                        "id": self.batch2.picking_ids.id,
                        "name": self.batch2.picking_ids.name,
                        "move_line_count": len(self.batch2.picking_ids.move_line_ids),
                        "origin": self.batch2.picking_ids.origin,
                        "weight": 6.0,
                        "partner": {
                            "id": self.batch2.picking_ids.partner_id.id,
                            "name": self.batch2.picking_ids.partner_id.name,
                        },
                    }
                ],
            },
        )

    def test_find_batch_unassigned_draft(self):
        """Find a draft batch"""
        # batches must have all their pickings available to be selected
        self._add_stock_and_assign_pickings_for_batches(self.batch2 | self.batch3)
        # batch1 has not all pickings available, so the first draft
        # is batch2, should be selected
        response = self.service.dispatch("find_batch")

        # The endpoint starts the batch and assign it to self
        self.assertEqual(self.batch2.user_id, self.env.user)
        self.assertEqual(self.batch2.state, "in_progress")

        # we expect to find batch 2 as it's the first one with all pickings
        # available
        self.assert_response(
            response,
            next_state="confirm_start",
            data={
                "id": self.batch2.id,
                "name": self.batch2.name,
                "pickings": [
                    {
                        "id": self.batch2.picking_ids.id,
                        "name": self.batch2.picking_ids.name,
                        "move_line_count": len(self.batch2.picking_ids.move_line_ids),
                        "origin": self.batch2.picking_ids.origin,
                        "weight": 6.0,
                        "partner": {
                            "id": self.batch2.picking_ids.partner_id.id,
                            "name": self.batch2.picking_ids.partner_id.name,
                        },
                    }
                ],
            },
        )

    def test_find_batch_not_found(self):
        """No batch to work on"""
        # No batch match the rules to work on them, because
        # their pickings are not available
        response = self.service.dispatch("find_batch")

        self.assert_response(
            response,
            next_state="start",
            message={
                "message_type": "info",
                "body": "No more work to do, please create a new batch transfer",
            },
        )

    def test_list_batch(self):
        """List all available batches"""
        # batches must have all their pickings available to be selected
        self._add_stock_and_assign_pickings_for_batches(
            self.batch1 | self.batch2 | self.batch3
        )
        self.batch1.write({"state": "in_progress", "user_id": self.env.uid})
        self.batch2.write(
            {"state": "in_progress", "user_id": self.env.ref("base.user_demo")}
        )
        self.batch3.write({"state": "draft", "user_id": False})

        self.assertEqual(
            self.env["stock.picking.batch"].search([]),
            self.batch1 + self.batch2 + self.batch3 + self.batch4,
        )
        # Simulate the client asking the list of batches
        response = self.service.dispatch("list_batch")
        self.assert_response(
            response,
            next_state="manual_selection",
            data={
                "size": 2,
                "records": [
                    {
                        "id": self.batch1.id,
                        "name": self.batch1.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                        "weight": 6.0,
                    },
                    # batch 2 is excluded because assigned to someone else
                    {
                        "id": self.batch3.id,
                        "name": self.batch3.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                        "weight": 6.0,
                    },
                    # batch 4 is excluded because not all of its pickings are
                    # assigned
                ],
            },
        )

    def test_select_in_progress_assigned(self):
        """Select an in-progress batch assigned to the current user"""
        self._add_stock_and_assign_pickings_for_batches(self.batch1)
        self.batch1.write({"state": "in_progress", "user_id": self.env.uid})
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "select", params={"picking_batch_id": self.batch1.id}
        )
        self.assert_response(
            response,
            next_state="confirm_start",
            data={
                "id": self.batch1.id,
                "name": self.batch1.name,
                # we don't care in these tests, the 'find_batch' tests already
                # check this
                "pickings": self.ANY,
            },
        )

    def test_select_draft_assigned(self):
        """Select a draft batch assigned to the current user"""
        self._add_stock_and_assign_pickings_for_batches(self.batch1)
        self.batch1.write({"user_id": self.env.uid})
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "select", params={"picking_batch_id": self.batch1.id}
        )
        # The endpoint starts the batch and assign it to self
        self.assertEqual(self.batch1.user_id, self.env.user)
        self.assertEqual(self.batch1.state, "in_progress")
        self.assert_response(
            response,
            next_state="confirm_start",
            data={
                "id": self.batch1.id,
                "name": self.batch1.name,
                # we don't care in these tests, the 'find_batch' tests already
                # check this
                "pickings": self.ANY,
            },
        )

    def test_select_draft_unassigned(self):
        """Select a draft batch not assigned to a user"""
        self._add_stock_and_assign_pickings_for_batches(self.batch1)
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "select", params={"picking_batch_id": self.batch1.id}
        )
        # The endpoint starts the batch and assign it to self
        self.assertEqual(self.batch1.user_id, self.env.user)
        self.assertEqual(self.batch1.state, "in_progress")
        self.assert_response(
            response,
            next_state="confirm_start",
            data={
                "id": self.batch1.id,
                "name": self.batch1.name,
                # we don't care in these tests, the 'find_batch' tests already
                # check this
                "pickings": self.ANY,
            },
        )

    def test_select_not_exists(self):
        """Select a draft that does not exist"""
        batch_id = self.batch1.id
        self.batch1.unlink()
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "select", params={"picking_batch_id": batch_id}
        )
        self.assert_response(
            response,
            next_state="manual_selection",
            message={
                "message_type": "warning",
                "body": "This batch cannot be selected.",
            },
            data={"size": 0, "records": []},
        )

    def test_select_already_assigned(self):
        """Select a draft that does not exist"""
        self._add_stock_and_assign_pickings_for_batches(self.batch1)
        self.batch1.write(
            {"state": "in_progress", "user_id": self.env.ref("base.user_demo")}
        )
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "select", params={"picking_batch_id": self.batch1.id}
        )
        self.assert_response(
            response,
            next_state="manual_selection",
            message={
                "message_type": "warning",
                "body": "This batch cannot be selected.",
            },
            data={"size": 0, "records": []},
        )

    def test_unassign_batch(self):
        """User cancels after selecting a batch, unassign it"""
        self._simulate_batch_selected(self.batch1)
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "unassign", params={"picking_batch_id": self.batch1.id}
        )
        self.assertEqual(self.batch1.state, "draft")
        self.assertFalse(self.batch1.user_id)
        self.assert_response(response, next_state="start")

    def test_unassign_batch_not_exists(self):
        """User cancels after selecting a batch deleted meanwhile"""
        batch_id = self.batch1.id
        self.batch1.unlink()
        # Simulate the client selecting the batch in a list
        response = self.service.dispatch(
            "unassign", params={"picking_batch_id": batch_id}
        )
        self.assert_response(response, next_state="start")


class ClusterPickingSelectedCase(ClusterPickingCommonCase):
    """Tests covering endpoints working on a single picking batch

    After a batch has been selected, by the tests covered in
    ``ClusterPickingSelectionCase``.
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls._simulate_batch_selected(cls.batch, in_package=True)

    def test_confirm_start_ok(self):
        """User confirms she starts the selected picking batch (happy path)"""
        # batch1 was already selected, we only need to confirm the selection
        batch = self.batch
        self.assertEqual(batch.state, "in_progress")
        picking = batch.picking_ids[0]
        first_move_line = picking.move_line_ids[0]
        self.assertTrue(first_move_line)
        # A package exists on the move line, because the quant created
        # by ``_simulate_batch_selected`` has a package.
        package = first_move_line.package_id
        self.assertTrue(package)

        response = self.service.dispatch(
            "confirm_start", params={"picking_batch_id": self.batch.id}
        )
        self.assert_response(
            response,
            data={
                "id": first_move_line.id,
                "quantity": 1.0,
                "postponed": False,
                "location_dest": {
                    "id": first_move_line.location_dest_id.id,
                    "name": first_move_line.location_dest_id.name,
                },
                "location_src": {
                    "id": first_move_line.location_id.id,
                    "name": first_move_line.location_id.name,
                },
                "picking": {
                    "id": picking.id,
                    "name": picking.name,
                    "note": None,
                    "origin": picking.origin,
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
                "batch": {"id": batch.id, "name": batch.name},
                "product": {
                    "default_code": first_move_line.product_id.default_code,
                    "display_name": first_move_line.product_id.display_name,
                    "id": first_move_line.product_id.id,
                    "name": first_move_line.product_id.name,
                    "qty_available": first_move_line.product_id.qty_available,
                },
                "lot": None,
                "package_src": {"id": package.id, "name": package.name},
            },
            next_state="start_line",
        )

    def test_confirm_start_not_exists(self):
        """User confirms she starts but batch has been deleted meanwhile"""
        batch_id = self.batch.id
        self.batch.unlink()
        response = self.service.dispatch(
            "confirm_start", params={"picking_batch_id": batch_id}
        )
        self.assert_response(
            response,
            message={
                "message_type": "error",
                "body": "The record you were working on does not exist anymore.",
            },
            next_state="start",
        )

    def test_confirm_start_all_is_done(self):
        """User confirms start but all lines are already done"""
        # we want to jump to the start because there are no lines
        # to process anymore, but we want to set pickings and
        # picking batch to done if not done yet (because the process
        # was interrupted for instance)
        self._set_dest_package_and_done(
            self.batch.mapped("picking_ids.move_line_ids"),
            self.env["stock.quant.package"].create({}),
        )
        self.batch.done()
        response = self.service.dispatch(
            "confirm_start", params={"picking_batch_id": self.batch.id}
        )
        self.assert_response(
            response,
            next_state="start",
            message={"body": "Batch Transfer complete", "message_type": "success"},
        )
