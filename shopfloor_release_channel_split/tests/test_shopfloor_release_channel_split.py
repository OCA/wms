# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.shopfloor.tests.common import CommonCase


# pylint: disable=missing-return
class TestActionsStockRelease(CommonCase):
    """Tests covering methods to work on stock operations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.work_on_actions(cls) as work:
            cls.stock = work.component(usage="stock")
        cls.product_a.tracking = "lot"
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)], confirm=True
        )
        cls.move0 = cls.picking.move_ids[0]
        cls.move1 = cls.picking.move_ids[1]
        cls._fill_stock_for_moves(cls.move0, in_lot=True)
        cls._fill_stock_for_moves(cls.move1)
        cls.picking.action_assign()

        cls.channel = (
            cls.env["stock.release.channel"]
            .sudo()
            .create({"name": "Test Release Split"})
        )
        cls.picking.release_channel_id = cls.channel

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id

    def test_unmark_move_line_as_picked_split_channel(self):
        """
        Mark line as picked and use the split strategy

        The release channel should be set
        """
        lines = self.picking.move_line_ids
        self.stock.mark_move_line_as_picked(lines[0], user=self.env.user)
        self.assertTrue(self.picking.backorder_ids)
        self.assertEqual(self.channel, self.picking.backorder_ids.release_channel_id)
