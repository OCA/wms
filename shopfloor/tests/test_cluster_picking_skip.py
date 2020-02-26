from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingSkipLineCase(ClusterPickingCommonCase):
    """Tests covering the /skip_line endpoint
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        # quants already existing are from demo data
        cls.env["stock.quant"].search(
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
        response = self.service.dispatch("skip_line", params={"move_line_id": line.id})
        if next_line:
            self.assert_response(
                response, next_state="start_line", data=self._line_data(next_line)
            )
        return response

    def test_skip_line(self):
        self._simulate_batch_selected(self.batch, in_package=True)
        lines = self.batch.picking_ids.move_line_ids
        # 1st line, next is 2nd
        self.assertFalse(lines[0].shopfloor_postponed)
        self._skip_line(lines[0], lines[1])
        self.assertTrue(lines[0].shopfloor_postponed)
        # 2nd line, next is 3rd
        self.assertFalse(lines[1].shopfloor_postponed)
        self._skip_line(lines[1], lines[2])
        self.assertTrue(lines[1].shopfloor_postponed)
        # 3rd line, next is 4th
        self.assertFalse(lines[2].shopfloor_postponed)
        self._skip_line(lines[2], lines[3])
        self.assertTrue(lines[2].shopfloor_postponed)
        # 4th line, next is 1st
        # the next line for the last one is the 1st,
        # because you'll have to process it anyway
        self.assertFalse(lines[3].shopfloor_postponed)
        self._skip_line(lines[3], lines[0])
        self.assertTrue(lines[3].shopfloor_postponed)


# TODO tests for transitions to next line / no next lines, ...
