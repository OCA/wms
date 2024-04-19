# Copyright 2024 vnikolayev1 Raumschmiede GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.tests import Form

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
        # Setting shopfloor.stock.action, partner, products
        with cls.work_on_actions(cls) as work:
            cls.stock = work.component(usage="stock")
        cls.res_partner = cls.env["res.partner"]
        cls.product_product = cls.env["product.product"]
        cls.product_1 = cls.product_product.sudo().create(
            {"name": "Product test 1", "type": "product"}
        )
        cls.product_2 = cls.product_product.sudo().create(
            {"name": "Product test 2", "type": "product"}
        )
        cls.partner = cls.res_partner.sudo().create({"name": "Partner test"})
        # setting sale order, canfirming it to create pickings
        order_form = Form(cls.env["sale.order"].sudo())
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product_1
            line_form.product_uom_qty = 10
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product_2
            line_form.product_uom_qty = 10
        cls.sale_order = order_form.save()
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.move0 = cls.picking.move_lines[0]
        cls.move1 = cls.picking.move_lines[1]
        # filling shopfloor.stock.action with moves
        cls._fill_stock_for_moves(cls.move0)
        cls._fill_stock_for_moves(cls.move1)
        cls.picking.action_assign()
        cls.picking._action_done()

    def test_create_return_move(self):
        # For incoming returns, moves are set to `to_refund`
        return_picking = self.stock.create_return_picking(
            self.picking, self.picking_type_in, "potato"
        )
        move_line = self.picking.move_lines[0]
        return_moves = self.stock.create_return_move(return_picking, move_line)
        self.assertEqual(return_moves.sale_line_id, move_line.sale_line_id)
        return_picking.action_assign()
        return_picking._action_done()
        outgoing_return = self.stock.create_return_picking(
            return_picking, self.picking_type, "potato"
        )
        outgoing_moves = self.stock.create_return_move(outgoing_return, return_moves)
        self.assertEqual(outgoing_moves.sale_line_id, move_line.sale_line_id)
