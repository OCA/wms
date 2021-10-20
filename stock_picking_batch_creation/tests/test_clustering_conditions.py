# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError

from .common import ClusterPickingCommonFeatures


class TestClusteringConditions(ClusterPickingCommonFeatures):
    @classmethod
    def setUpClass(cls):
        super(TestClusteringConditions, cls).setUpClass()
        cls.make_picking_batch = cls.makePickingBatch.create(
            {
                "user_id": cls.env.user.id,
                "picking_type_ids": [(4, cls.picking_type_1.id)],
                "stock_device_type_ids": [
                    (4, cls.device1.id),
                    (4, cls.device2.id),
                    (4, cls.device3.id),
                ],
            }
        )
        cls.p5 = cls._create_product("Unittest P5", 1, 4, 1, 1)

    def test_device_with_one_bin(self):
        candidates_pickings = self.make_picking_batch._search_pickings()
        device = self.make_picking_batch._compute_device_to_use(candidates_pickings[0])
        selected_pickings = self.make_picking_batch._check_number_of_available_bins(
            candidates_pickings[0], device
        )
        self.assertTrue(selected_pickings)
        self.assertEqual(selected_pickings[0], candidates_pickings[0])

    def test_first_pick_breaks_condition(self):
        self.p1.write({"volume": 5.0, "length": 5, "height": 1, "width": 1})
        self.p2.write({"volume": 3.0, "length": 3, "height": 1, "width": 1})
        picks = self._get_picks_by_type(self.picking_type_1)
        self._add_product_to_picking(picks[0], self.p5)
        self.make_picking_batch.write({"maximum_number_of_preparation_lines": 2})
        candidates_pickings = self.make_picking_batch._search_pickings()
        device = self.make_picking_batch._compute_device_to_use(candidates_pickings[0])
        selected_pickings = self.make_picking_batch._check_number_of_available_bins(
            candidates_pickings[0], device
        )
        self.assertFalse(selected_pickings)

        with self.assertRaises(UserError):
            self.make_picking_batch._check_first_picking(candidates_pickings[0], device)

    def test_put_3_pickings_in_one_cluster(self):
        self.p1.write(
            {"volume": 5.0, "length": 5, "height": 1, "width": 1, "weight": 1}
        )
        self.p2.write(
            {"volume": 5.0, "length": 5, "height": 1, "width": 1, "weight": 1}
        )
        picks = self._get_picks_by_type(self.picking_type_1)
        self._add_product_to_picking(picks[0], self.p5)
        self.make_picking_batch.write({"maximum_number_of_preparation_lines": 6})
        self._create_picking_pick_and_assign(
            self.picking_type_1.id, products=self.p1 | self.p5
        )
        candidates_pickings = self.make_picking_batch._search_pickings()
        device = self.make_picking_batch._compute_device_to_use(candidates_pickings[0])
        selected_pickings = self.make_picking_batch._check_number_of_available_bins(
            candidates_pickings[0], device
        )
        self.assertFalse(selected_pickings)
        self.make_picking_batch._check_first_picking(candidates_pickings[0], device)
        (
            selected_pickings,
            unselected_pickings,
        ) = self.make_picking_batch._apply_limits(candidates_pickings, device)
        self.assertTrue(selected_pickings)
        self.assertEqual(len(selected_pickings), 3)
        self.assertTrue(unselected_pickings)
        self.assertEqual(len(unselected_pickings), 1)

    def test_no_device_for_clustering(self):
        self.p1.write(
            {"volume": 200.0, "length": 200, "height": 1, "width": 1, "weight": 1}
        )
        self.p2.write(
            {"volume": 200.0, "length": 200, "height": 1, "width": 1, "weight": 1}
        )
        self.p5.write(
            {"volume": 200.0, "length": 200, "height": 1, "width": 1, "weight": 1}
        )
        picks = self._get_picks_by_type(self.picking_type_1)
        self._add_product_to_picking(picks[0], self.p5)
        self._create_picking_pick_and_assign(
            self.picking_type_1.id, products=self.p1 | self.p5
        )
        candidates_pickings = self.make_picking_batch._search_pickings()
        for picking in candidates_pickings:
            device = self.make_picking_batch._compute_device_to_use(picking)
            if device:
                break
        self.assertFalse(device)

        with self.assertRaises(UserError):
            self.make_picking_batch._create_batch()

    def test_one_picking_on_another_device(self):
        self.p1.write(
            {"volume": 10.0, "length": 10, "height": 1, "width": 1, "weight": 1}
        )
        self.p2.write(
            {"volume": 10.0, "length": 10, "height": 1, "width": 1, "weight": 1}
        )
        self.p5.write(
            {"volume": 120.0, "length": 120, "height": 1, "width": 1, "weight": 1}
        )
        self.device1.write({"nbr_bins": 8})
        self._create_picking_pick_and_assign(
            self.picking_type_1.id, products=self.p5, priority="0"
        )
        pick_on_another_device = self.env["stock.picking"].search(
            [("product_id", "=", self.p5.id)]
        )
        candidates_pickings = self.make_picking_batch._search_pickings()
        device = self.make_picking_batch._compute_device_to_use(candidates_pickings[0])
        (
            selected_pickings,
            unselected_pickings,
        ) = self.make_picking_batch._apply_limits(candidates_pickings, device)
        self.assertTrue(selected_pickings)
        self.assertEqual(len(selected_pickings), 3)
        self.assertTrue(unselected_pickings)
        self.assertEqual(len(unselected_pickings), 1)
        self.assertEqual(unselected_pickings, pick_on_another_device)
