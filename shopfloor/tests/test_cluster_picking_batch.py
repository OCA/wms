# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import CommonCase, PickingBatchMixin


class ClusterPickingBatchCase(CommonCase, PickingBatchMixin):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_cluster_picking")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.product_a = (
            cls.env["product.product"]
            .sudo()
            .create({"name": "Product A", "type": "product"})
        )
        cls.product_b = (
            cls.env["product.product"]
            .sudo()
            .create({"name": "Product B", "type": "product"})
        )
        cls.batch1 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls.batch2 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls.batch3 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_a, quantity=1)]]
        )
        cls.batch4 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_b, quantity=1)]]
        )
        cls.batch5 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_b, quantity=1)]]
        )
        cls.batch6 = cls._create_picking_batch(
            [[cls.BatchProduct(product=cls.product_b, quantity=1)]]
        )
        cls.all_batches = (
            cls.batch1 + cls.batch2 + cls.batch3 + cls.batch4 + cls.batch5 + cls.batch6
        )

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "cluster_picking", menu=self.menu, profile=self.profile
        )

    def test_search_empty(self):
        """No batch is available"""
        # Simulate the client asking the list of picking batch
        # none of the pickings are assigned, so we can't work on them
        self.assertFalse(self.service._batch_picking_search())

    def test_search(self):
        """Return only draft batches with assigned pickings"""
        pickings = self.all_batches.mapped("picking_ids")
        self._fill_stock_for_moves(pickings.mapped("move_lines"))
        pickings.action_assign()
        self.assertTrue(all(p.state == "assigned" for p in pickings))
        # we should not have done batches in list
        self.batch5.state = "done"
        # nor canceled batches
        self.batch6.state = "cancel"
        # we should not have batches in progress
        self.batch4.user_id = self.env.ref("base.user_demo")
        self.batch4.action_confirm()
        # unless it's assigned to our user
        self.batch3.user_id = self.env.user
        self.batch3.action_confirm()

        # Simulate the client asking the list of picking batch
        res = self.service._batch_picking_search()
        self.assertRecordValues(
            res,
            [
                {
                    "id": self.batch1.id,
                    "name": self.batch1.name,
                    "picking_count": 1,
                    "move_line_count": 1,
                    "total_weight": 0.0,
                },
                {
                    "id": self.batch2.id,
                    "name": self.batch2.name,
                    "picking_count": 1,
                    "move_line_count": 1,
                    "total_weight": 0.0,
                },
                {
                    "id": self.batch3.id,
                    "name": self.batch3.name,
                    "picking_count": 1,
                    "move_line_count": 1,
                    "total_weight": 0.0,
                },
            ],
        )
