# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# pylint: disable=missing-return


from .common import CommonCase


class TestActionsPackaging(CommonCase):
    """Tests covering methods to work on product packaging."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.work_on_actions(cls) as work:
            cls.packaging = work.component(usage="packaging")
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)], confirm=True
        )
        cls.move0 = cls.picking.move_ids[0]
        cls.move1 = cls.picking.move_ids[1]
        cls._fill_stock_for_moves(
            cls.picking.move_ids, in_package=True, same_package=True
        )
        cls.picking.action_assign()
        cls.package1 = cls.move0.move_line_ids.package_id

    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id

    def test_package_is_complete_mix_pack(self):
        self.assertTrue(self.packaging.is_complete_mix_pack(self.package1))

    def test_package_partially_reserved(self):
        # Package has 2 products from pick 1 reserved
        pick2 = self._create_picking(lines=[(self.product_c, 10)], confirm=True)
        # But adding 1 more product from pick 2 that is not yet reserved
        self._fill_stock_for_moves(pick2.move_ids, in_package=self.package1)
        self.assertFalse(self.packaging.is_complete_mix_pack(self.package1))
