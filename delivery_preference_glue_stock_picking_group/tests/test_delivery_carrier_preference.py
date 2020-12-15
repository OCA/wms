# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form

from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)


class TestDeliveryPreferenceGlueStockPickingGroup(PromiseReleaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ref = cls.env.ref
        cls.partner = ref("base.res_partner_12")
        cls.product = ref("product.product_product_20")
        cls.product.write({"weight": 10.0})

        cls.the_poste_carrier = ref("delivery.delivery_carrier")
        cls.normal_delivery_carrier = ref("delivery.normal_delivery_carrier")
        cls.env["delivery.carrier.preference"].create(
            {
                "sequence": 10,
                "preference": "carrier",
                "carrier_id": cls.normal_delivery_carrier.id,
                "max_weight": 20.0,
            }
        )
        cls.theposte = cls.env["delivery.carrier.preference"].create(
            {
                "sequence": 20,
                "preference": "carrier",
                "carrier_id": cls.the_poste_carrier.id,
                "max_weight": 40.0,
            }
        )
        cls.wh.delivery_route_id.write(
            {
                "available_to_promise_defer_pull": True,
                "force_recompute_preferred_carrier_on_release": True,
            }
        )
        cls.wh.group_shippings = True

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

    def test_delivery_release_available_to_promise_two_sale_order(self):
        """
        Customer with the_poste as delivery carrier by default.
        And the poste carrier is not in preferences.
        Two sale order confirmed for the same product.
        There is enough stock to ship some of the first order.
        Check that the backorder created as the customer default
        delivery carrier. When the picking for the available delivery
        has the preferred delivery carrier.
        """
        self.theposte.unlink()
        self.partner.property_delivery_carrier_id = self.the_poste_carrier
        order1 = self._create_sale_order()
        self._update_order_line_qty(order1, 3)
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.loc_stock, 2
        )
        self._add_shipping_on_order(order1)
        order1.action_confirm()
        delivery_pick = order1.picking_ids
        self.assertEqual(order1.carrier_id, self.the_poste_carrier)
        order2 = self._create_sale_order()
        self._update_order_line_qty(order2, 3)
        self._add_shipping_on_order(order2)
        self.assertEqual(order2.carrier_id, self.the_poste_carrier)
        order2.action_confirm()
        # Release the first goods
        delivery_pick = order1.picking_ids
        delivery_pick.release_available_to_promise()
        picking_out = order1.picking_ids.filtered(
            lambda r: r.picking_type_id.code == "outgoing" and not r.backorder_id
        )
        picking_backorder = order1.picking_ids.filtered(lambda r: r.backorder_id)
        # The OUT picking has the prefered carrier for 20kg (normal carrier)
        # self.assertAlmostEqual(picking_out.estimated_shipping_weight, 20.0)
        self.assertEqual(picking_out.carrier_id, self.normal_delivery_carrier)
        # Backorder picking should have the partner default carrier (the poste)
        self.assertEqual(picking_backorder.carrier_id, self.the_poste_carrier)
