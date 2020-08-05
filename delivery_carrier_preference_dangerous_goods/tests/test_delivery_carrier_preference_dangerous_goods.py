# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.delivery_carrier_preference.tests.test_delivery_carrier_preference import (  # noqa
    TestSaleDeliveryCarrierPreference,
)


class TestSaleDeliveryCarrierPreferenceDangerousGoods(
    TestSaleDeliveryCarrierPreference
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.normal_delivery_carrier.write({"dangerous_goods_warning": True})
        cls.super_fast_carrier.write({"dangerous_goods_warning": True})
        cls.env["delivery.carrier.preference"].create(
            {"sequence": 15, "preference": "partner", "max_weight": 15.0}
        )
        cls.product.write({"is_dangerous_good": True})

    def test_delivery_add_preferred_carrier_dangerous_goods(self):
        """
        With a qty of 1 in the sale order and 3 available to promise,
        estimated_shipping_weight is 10, but as both of the first preferred
        carriers (carrier-normal and partner-super fast) do not accept dangerous
        goods, it must select 'the poste'
        """
        order = self._create_sale_order()
        self._update_order_line_qty(order, 1)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.loc_stock, 1
        )
        order.action_confirm()
        delivery_pick = order.picking_ids
        self.assertAlmostEqual(delivery_pick.estimated_shipping_weight, 10.0)
        delivery_pick.add_preferred_carrier()
        self.assertEqual(delivery_pick.carrier_id, self.the_poste_carrier)
