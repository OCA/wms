# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from .common import PRIORITY_NORMAL, DeliveryCarrierPreferenceCommon


class TestSaleDeliveryCarrierPreference(DeliveryCarrierPreferenceCommon):
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
        estimated_shipping_weight is 50, and with a priority of 0, preferred
        carrier must be free
        """
        order = self._create_sale_order()
        self._update_order_line_qty(order, 5)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.loc_stock, 5
        )
        order.action_confirm()
        delivery_pick = order.picking_ids
        self.assertEqual(delivery_pick.priority, PRIORITY_NORMAL)
        self.assertAlmostEqual(delivery_pick.estimated_shipping_weight, 50.0)
        delivery_pick.add_preferred_carrier()
        self.assertEqual(delivery_pick.carrier_id, self.free_delivery_carrier)
