# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopfloor.tests.test_cluster_picking_base import (
    ClusterPickingCommonCase,
)


# pylint: disable=missing-return
class ClusterPickingLossQuantityStockIssueCase(ClusterPickingCommonCase):
    """Test /stock_issue with the `loss_quantity` stock issue strategy."""

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.menu.sudo().stock_issue_strategy = "loss_quantity"
        cls.wh.sudo().use_loss_picking = True
        cls._update_qty_in_location(cls.stock_location, cls.product_a, 10)
        cls._update_qty_in_location(cls.stock_location, cls.product_b, 10)
        # Two lines in the batch: after the stock issue empties the first
        # one, the batch is not fully done yet (the second line remains),
        # which keeps the rest of the cluster picking flow (unload/closing
        # the batch) out of the way of this test.
        cls.batch = cls._create_picking_batch(
            [
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
                [cls.BatchProduct(product=cls.product_b, quantity=10)],
            ]
        )

    def test_stock_issue_declares_a_loss(self):
        """Declaring a stock issue locks the quant behind a move of the
        warehouse's Loss operation type, instead of silently correcting
        the inventory count.
        """
        move_line = self.batch.picking_ids.move_line_ids.filtered(
            lambda line: line.product_id == self.product_a
        )
        move = move_line.move_id
        product = move.product_id
        location = move_line.location_id
        package = move_line.package_id

        self.service.dispatch(
            "stock_issue",
            params={"picking_batch_id": self.batch.id, "move_line_id": move_line.id},
        )

        quant = self.env["stock.quant"]._gather(
            product, location, package_id=package, strict=True
        )
        self.assertTrue(quant.is_locked_by_picking)
        loss_picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", self.wh.loss_type_id.id)]
        )
        self.assertEqual(len(loss_picking), 1)
        self.assertEqual(loss_picking.move_ids.quant_lock_quant_id, quant)
