# Copyright 2024 ACSONE SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-return
from contextlib import contextmanager

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext

from .common import CommonCase


class TestActionsSearchMoveLine(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking_user1 = cls._create_picking(
            lines=[(cls.product_a, 10)], confirm=True
        )
        cls.picking_user2 = cls._create_picking(
            lines=[(cls.product_a, 10)], confirm=True
        )
        cls.picking_no_user = cls._create_picking(
            lines=[(cls.product_a, 10)], confirm=True
        )

        cls.pickings = cls.picking_no_user | cls.picking_user1 | cls.picking_user2
        cls._fill_stock_for_moves(cls.pickings.move_ids)
        cls.pickings.action_assign()
        cls.move_lines = cls.pickings.move_line_ids
        cls.user1 = cls.env.user.copy({"name": "User 1", "login": "user1"})
        cls.user2 = cls.env.user.copy({"name": "User 2", "login": "user2"})
        cls.picking_no_user.user_id = False
        cls.picking_user1.user_id = cls.user1.id
        cls.picking_user2.move_line_ids.write({"shopfloor_user_id": cls.user2.id})
        cls.picking_user2.user_id = cls.user2.id

    @contextmanager
    def work_on_actions(self, user=None, **params):
        params = params or {}
        env = self.env(user=user) if user else self.env
        collection = _PseudoCollection("shopfloor.action", env)
        yield WorkContext(
            model_name="rest.service.registration", collection=collection, **params
        )

    @contextmanager
    def search_move_line(self, user=None):
        with self.work_on_actions(user) as work:
            move_line_search = work.component(usage="search_move_line")
            yield move_line_search

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id

    def test_search_move_line_sorter(self):
        with self.search_move_line() as move_line_search:
            move_lines = self.move_lines.sorted(
                move_line_search._sort_key_move_lines(order="assigned_to_current_user")
            )
        # we must get operations in the following order:
        #  * no shopfloor user and not user assigned to picking
        #  * no shopfloor user and user assigned to picking
        #  * shopfloor user or user assigned to picking

        self.assertFalse(move_lines[0].shopfloor_user_id)
        self.assertFalse(move_lines[0].picking_id.user_id)
        self.assertFalse(move_lines[1].shopfloor_user_id)
        self.assertTrue(move_lines[1].picking_id.user_id)
        self.assertTrue(move_lines[2].shopfloor_user_id)

        with self.search_move_line(user=self.user1) as move_line_search:
            move_lines = self.move_lines.sorted(
                move_line_search._sort_key_move_lines(order="assigned_to_current_user")
            )
        # user1 is only assigned at picking level
        # we must get operations in the following order:
        # * no shopfloor user but user assigned to picking
        # * no shopfloor user and not user assigned to picking
        # * shopfloor user or user assigned to picking
        self.assertFalse(move_lines[0].shopfloor_user_id)
        self.assertEqual(move_lines[0].picking_id.user_id, self.user1)
        self.assertFalse(move_lines[1].shopfloor_user_id)
        self.assertTrue(move_lines[2].shopfloor_user_id)

        with self.search_move_line(user=self.user2) as move_line_search:
            move_lines = self.move_lines.sorted(
                move_line_search._sort_key_move_lines(order="assigned_to_current_user")
            )
        # user2 is only assigned at move level
        # we must get operations in the following order:
        # * shopfloor user or user assigned to picking
        # * no shopfloor user and no user assigned to picking
        # * no shopfloor user and user assigned to picking
        self.assertEqual(move_lines[0].shopfloor_user_id, self.user2)
        self.assertFalse(move_lines[1].shopfloor_user_id)
        self.assertFalse(move_lines[1].picking_id.user_id)
        self.assertTrue(move_lines[2].picking_id.user_id)

    def test_search_move_line_match_user(self):
        with self.search_move_line() as move_line_search:
            move_lines = move_line_search.search_move_lines(
                locations=self.picking_type.default_location_src_id,
                match_user=True,
            )
        # we must only get picking not assigned to a user
        self.assertFalse(move_lines.picking_id.user_id)
        self.assertFalse(move_lines.shopfloor_user_id)

        with self.search_move_line(user=self.user1) as move_line_search:
            move_lines = move_line_search.search_move_lines(
                locations=self.picking_type.default_location_src_id,
                match_user=True,
            )
        # we must only get picking assigned to user1 or not assigned to any user
        self.assertEqual(move_lines.picking_id.user_id, self.user1)
        self.assertFalse(move_lines.shopfloor_user_id)

        with self.search_move_line(user=self.user2) as move_line_search:
            move_lines = move_line_search.search_move_lines(
                locations=self.picking_type.default_location_src_id,
                match_user=True,
            )
        # we must only get picking assigned to user2
        self.assertEqual(move_lines.picking_id.user_id, self.user2)
        self.assertEqual(move_lines.shopfloor_user_id, self.user2)
