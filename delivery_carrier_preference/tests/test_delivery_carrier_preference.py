# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form

from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class TestSaleDeliveryCarrierPreference(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.partner = ref("base.res_partner_12")
        cls.product = ref("product.product_product_20")
        cls.product.write({"weight": 10.0})

        cls.free_delivery_carrier = ref("delivery.free_delivery_carrier")
        cls.the_poste_carrier = ref("delivery.delivery_carrier")
        cls.normal_delivery_carrier = ref("delivery.normal_delivery_carrier")
        cls.super_fast_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Super fast carrier",
                "product_id": cls.free_delivery_carrier.product_id.id,
            }
        )
        cls.partner.write({"property_delivery_carrier_id": cls.super_fast_carrier.id})
        cls.env["delivery.carrier.preference"].create(
            {
                "sequence": 10,
                "preference": "carrier",
                "carrier_id": cls.normal_delivery_carrier.id,
                "max_weight": 20.0,
            }
        )
        cls.env["delivery.carrier.preference"].create(
            {
                "sequence": 20,
                "preference": "carrier",
                "carrier_id": cls.the_poste_carrier.id,
                "max_weight": 40.0,
            }
        )
        cls.env["delivery.carrier.preference"].create(
            {
                "sequence": 30,
                "preference": "carrier",
                "carrier_id": cls.super_fast_carrier.id,
                "max_weight": 0.0,
                "picking_domain": "[('priority', '=', '3')]",
            }
        )
        cls.env["delivery.carrier.preference"].create(
            {
                "sequence": 40,
                "preference": "carrier",
                "carrier_id": cls.free_delivery_carrier.id,
                "max_weight": 0.0,
            }
        )
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
                "force_recompute_preferred_carrier_on_release": True,
            }
        )
        cls.outgoing_pick_type = cls.wh.out_type_id

    @classmethod
    def _create_sale_order(cls):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        sale_form.warehouse_id = cls.wh
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 2
        return sale_form.save()

    @classmethod
    def _update_order_line_qty(cls, order, qty):
        with Form(order) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = qty

    @classmethod
    def _add_shipping_on_order(cls, order, carrier=None):
        delivery_wiz_action = order.action_open_delivery_wizard()
        delivery_wiz_context = delivery_wiz_action.get("context", {})
        if carrier is not None:
            delivery_wiz_context["default_carrier_id"] = carrier.id
        delivery_wiz = (
            cls.env[delivery_wiz_action.get("res_model")]
            .with_context(**delivery_wiz_context)
            .create({})
        )
        delivery_wiz.button_confirm()

    def test_delivery_add_preferred_carrier(self):
        """
        With a qty of 5 in the sale order and only 3 available to promise,
        estimated_shipping_weight is 30, and preferred carrier 'the poste'
        """
        order = self._create_sale_order()
        self._update_order_line_qty(order, 5)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.loc_stock, 3
        )
        order.action_confirm()
        delivery_pick = order.picking_ids
        self.assertAlmostEqual(delivery_pick.estimated_shipping_weight, 30.0)
        delivery_pick.add_preferred_carrier()
        self.assertEqual(delivery_pick.carrier_id, self.the_poste_carrier)

    def test_delivery_release_available_to_promise(self):
        """
        With carrier 'super fast' and a qty of 3 in the sale order,
        only 2 available to promise, estimated_shipping_weight is 20.0,
        so preferred carrier after the release is 'normal' and backorder get
        'super fast'
        """
        order = self._create_sale_order()
        self._update_order_line_qty(order, 3)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.loc_stock, 2
        )
        self._add_shipping_on_order(order)
        self.assertEqual(order.carrier_id, self.super_fast_carrier)
        order.action_confirm()
        delivery_pick = order.picking_ids
        self.assertAlmostEqual(delivery_pick.estimated_shipping_weight, 20.0)
        delivery_pick.release_available_to_promise()
        self.assertEqual(delivery_pick.carrier_id, self.normal_delivery_carrier)
        self.assertEqual(
            delivery_pick.group_id.carrier_id, self.normal_delivery_carrier
        )
        backorder = delivery_pick.backorder_ids
        self.assertEqual(backorder.carrier_id, self.super_fast_carrier)
        self.assertEqual(backorder.group_id.carrier_id, self.super_fast_carrier)

    def test_delivery_add_preferred_carrier_picking_domain(self):
        """
        With a qty of 5 in the sale order and 5 available to promise,
        estimated_shipping_weight is 50, and with a priority of 2, preferred
        carrier must be free
        """
        order = self._create_sale_order()
        self._update_order_line_qty(order, 5)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.loc_stock, 5
        )
        order.action_confirm()
        delivery_pick = order.picking_ids
        self.assertEqual(delivery_pick.priority, "1")
        self.assertAlmostEqual(delivery_pick.estimated_shipping_weight, 50.0)
        delivery_pick.add_preferred_carrier()
        self.assertEqual(delivery_pick.carrier_id, self.free_delivery_carrier)
