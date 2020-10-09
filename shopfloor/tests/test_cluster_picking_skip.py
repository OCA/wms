# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingSkipLineCase(ClusterPickingCommonCase):
    """Tests covering the /skip_line endpoint
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # quants already existing are from demo data
        cls.env["stock.quant"].sudo().search(
            [("location_id", "=", cls.stock_location.id)]
        ).unlink()
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=20),
                ],
                [
                    cls.BatchProduct(product=cls.product_a, quantity=30),
                    cls.BatchProduct(product=cls.product_b, quantity=40),
                ],
            ]
        )

    def _skip_line(self, line, next_line=None):
        response = self.service.dispatch(
            "skip_line",
            params={"picking_batch_id": self.batch.id, "move_line_id": line.id},
        )
        if next_line:
            self.assert_response(
                response, next_state="start_line", data=self._line_data(next_line)
            )
        return response

    def test_skip_line(self):
        # put one picking in another location
        self.batch.picking_ids[1].location_id = self.shelf1
        self.batch.picking_ids[1].move_lines.location_id = self.shelf1
        # select batch
        self._simulate_batch_selected(self.batch, in_package=True)

        # enforce names to have reliable sorting
        self.stock_location.sudo().name = "LOC2"
        self.shelf1.sudo().name = "LOC1"
        all_lines = self.batch.picking_ids.move_line_ids
        loc1_lines = all_lines.filtered(lambda line: (line.location_id == self.shelf1))
        loc2_lines = all_lines.filtered(
            lambda line: (line.location_id == self.stock_location)
        )
        # no line postponed yet
        self.assertEqual(
            all_lines.mapped("shopfloor_postponed"), [False, False, False, False]
        )

        # skip line from loc 1
        self._skip_line(loc1_lines[0], loc1_lines[1])
        self.assertTrue(loc1_lines[0].shopfloor_postponed)

        # 2nd line, next is 1st from 2nd location
        self.assertFalse(loc1_lines[1].shopfloor_postponed)
        self._skip_line(loc1_lines[1], loc2_lines[0])
        self.assertTrue(loc1_lines[1].shopfloor_postponed)

        # 3rd line, next is 4th
        self.assertFalse(loc2_lines[0].shopfloor_postponed)
        self._skip_line(loc2_lines[0], loc2_lines[1])
        self.assertTrue(loc2_lines[0].shopfloor_postponed)


# TODO tests for transitions to next line / no next lines, ...
