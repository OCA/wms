# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# from odoo.tests.common import Form

from .common import CommonCase


# pylint: disable=missing-return
class TestActionsStock(CommonCase):
    """Tests covering methods to work on stock operations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.work_on_actions(cls) as work:
            cls.stock = work.component(usage="stock")
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)], confirm=True
        )
        cls.move0 = cls.picking.move_ids[0]
        cls.move1 = cls.picking.move_ids[1]
        cls._fill_stock_for_moves(cls.move0)
        cls._fill_stock_for_moves(cls.move1)
        cls.picking.action_assign()

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id

    def test_unmark_move_line_as_picked(self):
        """Check unmarking line as picked works."""
        lines_picked = self.picking.move_line_ids
        # all lines (two) are picked
        self.stock.mark_move_line_as_picked(lines_picked)
        self.assertTrue(self.picking.user_id)
        # unpick one line
        line_unpicked = lines_picked[0]
        self.stock.unmark_move_line_as_picked(line_unpicked)
        # because not all lines of the picking have to be unpicked
        # they should be split to a new picking
        picking_not_assigned = line_unpicked.picking_id
        self.assertTrue(line_unpicked.picking_id != lines_picked.picking_id)
        self.assertTrue(self.picking.user_id)
        self.assertTrue(self.picking.move_line_ids.shopfloor_user_id)
        self.assertFalse(picking_not_assigned.move_line_ids.shopfloor_user_id)
        self.assertFalse(picking_not_assigned.user_id)
