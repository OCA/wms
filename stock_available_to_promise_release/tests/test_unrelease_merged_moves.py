# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from datetime import datetime

from .common import PromiseReleaseCommonCase


class TestAvailableToPromiseRelease(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        delivery_pick_rule = cls.wh.delivery_route_id.rule_ids.filtered(
            lambda r: r.location_src_id == cls.loc_stock
        )
        delivery_pick_rule.group_propagation_option = "fixed"
        cls.pc1 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 2)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.shipping1 = cls._out_picking(cls.pc1)
        cls.pc2 = cls._create_picking_chain(
            cls.wh, [(cls.product1, 3)], date=datetime(2019, 9, 2, 16, 0)
        )
        cls.shipping2 = cls._out_picking(cls.pc2)
        cls._update_qty_in_location(cls.loc_bin1, cls.product1, 15.0)
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
            }
        )
        shippings = cls.shipping1 | cls.shipping2
        shippings.release_available_to_promise()
        cls.picking1 = cls._prev_picking(cls.shipping1)
        cls.picking1.action_assign()
        cls.picking2 = cls._prev_picking(cls.shipping2)
        cls.picking2.action_assign()

    @classmethod
    def _out_picking(cls, pickings):
        return pickings.filtered(lambda r: r.picking_type_code == "outgoing")

    @classmethod
    def _prev_picking(cls, picking):
        return picking.move_ids.move_orig_ids.picking_id

    def test_unrelease_merged_move(self):
        self.assertEqual(self.picking1, self.picking2)
        moves = self.picking1.move_ids.filtered(lambda m: m.state == "assigned")
        self.assertEqual(sum(moves.mapped("product_uom_qty")), 5.0)
        self.shipping2.unrelease()
        move = self.picking1.move_ids.filtered(lambda m: m.state == "assigned")
        line = move.move_line_ids
        self.assertEqual(move.product_uom_qty, 2.0)
        self.assertEqual(line.reserved_uom_qty, 2.0)
