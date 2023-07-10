# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.common import CommonCase


class TestActionsStock(CommonCase):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.location_customers = cls.env.ref("stock.stock_location_customers")
        cls.picking_type = cls.wh.out_type_id
        cls.picking_type.sudo().write(
            {"default_location_dest_id": cls.location_customers.id}
        )
        cls.picking_type_in = cls.picking_type.return_picking_type_id
        cls.picking_type_in.sudo().write(
            {"default_location_src_id": cls.location_customers.id}
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls.work_on_actions(cls) as work:
            cls.stock = work.component(usage="stock")
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)], confirm=True
        )
        cls.move0 = cls.picking.move_lines[0]
        cls.move1 = cls.picking.move_lines[1]
        cls._fill_stock_for_moves(cls.move0)
        cls._fill_stock_for_moves(cls.move1)
        cls.picking.action_assign()
        cls.picking._action_done()

    def test_create_return_move(self):
        # For incoming returns, moves are set to `to_refund`
        return_picking = self.stock.create_return_picking(
            self.picking, self.picking_type_in, "potato"
        )
        return_moves = self.stock.create_return_move(
            return_picking, self.picking.move_lines
        )
        self.assertTrue(all(move.to_refund for move in return_moves))
        return_picking.action_assign()
        return_picking._action_done()

        # However, on outgoing returns, this field is False
        outgoing_return = self.stock.create_return_picking(
            return_picking, self.picking_type, "potato"
        )
        outgoing_moves = self.stock.create_return_move(outgoing_return, return_moves)
        self.assertTrue(all(not move.to_refund for move in outgoing_moves))
