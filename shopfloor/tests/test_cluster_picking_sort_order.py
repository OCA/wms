# Copyright 2023 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import tagged

from .test_cluster_picking_base import ClusterPickingCommonCase


@tagged("post_install", "-at_install")
class ClusterPickingSortOrder(ClusterPickingCommonCase):
    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [cls.BatchProduct(product=cls.product_a, quantity=1)],
                [cls.BatchProduct(product=cls.product_b, quantity=1)],
                [cls.BatchProduct(product=cls.product_d, quantity=1)],
                [cls.BatchProduct(product=cls.product_c, quantity=1)],
                [cls.BatchProduct(product=cls.product_b, quantity=1)],
            ]
        )
        cls._simulate_batch_selected(cls.batch, in_package=True)
        cls.menu.sudo().move_line_processing_sort_order = "location_grouped_product"
        return

    def test_custom_lines_order(self):
        """The sorting of the lines in the batch groups lines with the same product"""
        batch = self.batch

        expected_lines_order = self._assign_different_locations(batch)

        for expected_line in expected_lines_order:
            # We are going to call this empoint once per line
            # to simulate the fact that the lines have to be treated
            # one at a time.
            response = self.service.dispatch(
                "confirm_start",
                params={"picking_batch_id": batch.id},
            )
            returned_line = batch.move_line_ids.filtered(
                lambda line: line.id == response["data"]["start_line"]["id"]
            )
            self.assertEqual(returned_line.id, expected_line.id)
            returned_line.state = "confirmed"

    def _assign_different_locations(self, batch):
        # We assign one unique location to each line of the batch
        # and we make sure each location has the sequence required for the test.
        locations = self.env["stock.location"].search([], limit=5)
        # The line with product A will have the lowest sequence.
        line_product_a = batch.move_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        line_product_a.location_id = locations[0]
        line_product_a.location_id.shopfloor_picking_sequence = 1
        line_product_a.state = "assigned"

        # One of the lines with product B will have the second lowest sequence.
        line_product_b_1 = fields.first(
            batch.move_line_ids.filtered(lambda line: line.product_id == self.product_b)
        )
        line_product_b_1.location_id = locations[1]
        line_product_b_1.location_id.shopfloor_picking_sequence = 2
        line_product_b_1.state = "assigned"

        # The line with product D will have the third lowest sequence.
        line_product_d = batch.move_line_ids.filtered(
            lambda line: line.product_id == self.product_d
        )
        line_product_d.location_id = locations[2]
        line_product_d.location_id.shopfloor_picking_sequence = 3
        line_product_d.state = "assigned"

        # The line with product C will have the second highest sequence.
        line_product_c = batch.move_line_ids.filtered(
            lambda line: line.product_id == self.product_c
        )
        line_product_c.location_id = locations[3]
        line_product_c.location_id.shopfloor_picking_sequence = 4
        line_product_c.state = "assigned"

        # The other line with product B will have the highest sequence.
        line_product_b_2 = batch.move_line_ids.filtered(
            lambda line: line.product_id == self.product_b
            and line.location_id != locations[1]
        )
        line_product_b_2.location_id = locations[4]
        line_product_b_2.location_id.shopfloor_picking_sequence = 5
        line_product_b_2.state = "assigned"

        # Return the lines in the order we expect once we sort by product.
        return (
            line_product_a,
            line_product_b_1,
            line_product_b_2,
            line_product_d,
            line_product_c,
        )
