# Copyright 2025 Camptocamp SA, BCIM
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests import tagged
from odoo.tests.common import Form

from odoo.addons.stock_warehouse_flow.tests.common import CommonFlow


@tagged("-at_install", "post_install")
class TestDeliveryRefresh(CommonFlow):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Set outgoing rules as
        out_rules = cls.env["stock.rule"].search(
            [("picking_type_id.code", "=", "outgoing")]
        )
        out_rules.route_id.available_to_promise_defer_pull = True
        cls.customer = cls.env["res.partner"].create({"name": "Bob the customer"})

    @classmethod
    def create_sale_order(cls, product_qty, carrier=None):
        with Form(cls.env["sale.order"]) as sale_form:
            sale_form.partner_id = cls.customer
            for product, qty in product_qty:
                with sale_form.order_line.new() as line:
                    line.product_id = product
                    line.product_uom_qty = qty
        order = sale_form.save()
        if carrier:
            cls.update_carrier_on_order(order, carrier)
        return order

    @classmethod
    def update_carrier_on_order(cls, order, carrier):
        order.set_delivery_line(carrier, 1)

    def test_flow_refresh_after_delivery_change(self):
        self.env.ref("stock.stock_location_stock")
        post_carrier_flow = self._get_flow("pick_ship")
        normal_carrier_flow = self._get_flow("pick_pack_ship")
        order = self.create_sale_order(
            [(self.product, 10)], carrier=post_carrier_flow.carrier_ids
        )
        order.action_confirm()
        picking = order.picking_ids
        move = picking.move_ids
        self.assertEqual(move.picking_type_id, post_carrier_flow.to_picking_type_id)
        # # Updating the carrier on the order should update flow used by moves
        self.update_carrier_on_order(order, normal_carrier_flow.carrier_ids)
        self.assertEqual(move.picking_type_id, normal_carrier_flow.to_picking_type_id)
