from odoo.tests.common import Form

from .common import CommonCase


class ClusterPickingCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.process.picking_type_ids
        cls.batch1 = cls._create_picking_batch(cls.product_a)
        cls.batch2 = cls._create_picking_batch(cls.product_a)
        cls.batch3 = cls._create_picking_batch(cls.product_a)

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="cluster_picking")

    @classmethod
    def _create_picking_batch(cls, product):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.picking_type
        picking_form.location_id = cls.stock_location
        picking_form.location_dest_id = cls.packing_location
        picking_form.origin = "test {}".format(product.name)
        picking_form.partner_id = cls.customer
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = product
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()

        batch_form = Form(cls.env["stock.picking.batch"])
        batch_form.picking_ids.add(picking)
        return batch_form.save()

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()

    def _add_stock_and_assign_pickings_for_batches(self, batches):
        pickings = batches.mapped("picking_ids")
        self._fill_stock_for_pickings(pickings)
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
                # TODO
                "weight": 0,
                "pickings": [
                    {
                        "id": self.batch3.picking_ids.id,
                        "name": self.batch3.picking_ids.name,
                        "move_line_count": len(self.batch3.picking_ids.move_line_ids),
                        "origin": self.batch3.picking_ids.origin,
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
                # TODO
                "weight": 0,
                "pickings": [
                    {
                        "id": self.batch2.picking_ids.id,
                        "name": self.batch2.picking_ids.name,
                        "move_line_count": len(self.batch2.picking_ids.move_line_ids),
                        "origin": self.batch2.picking_ids.origin,
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
                # TODO
                "weight": 0,
                "pickings": [
                    {
                        "id": self.batch2.picking_ids.id,
                        "name": self.batch2.picking_ids.name,
                        "move_line_count": len(self.batch2.picking_ids.move_line_ids),
                        "origin": self.batch2.picking_ids.origin,
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
                "message": "No more work to do, please create a new batch transfer",
            },
        )
