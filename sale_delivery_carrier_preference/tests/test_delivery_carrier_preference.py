# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form, SavepointCase


class TestSaleDeliveryCarrierPreference(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        ref = cls.env.ref
        cls.partner = ref("base.res_partner_12")
        cls.product = ref("product.product_product_20")
        cls.product.write({"weight": 10.0})
        cls.free_delivery_carrier = ref("delivery.free_delivery_carrier")
        cls.the_poste_carrier = ref("delivery.delivery_carrier")
        cls.normal_delivery_carrier = ref("delivery.normal_delivery_carrier")
        cls.partner_specific_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Partner specific",
                "product_id": cls.free_delivery_carrier.product_id.id,
            }
        )
        cls.partner.write(
            {"property_delivery_carrier_id": cls.partner_specific_carrier.id}
        )
        cls.env["sale.delivery.carrier.preference"].create(
            {
                "sequence": 10,
                "preference": "carrier",
                "carrier_id": cls.normal_delivery_carrier.id,
                "sale_order_max_weight": 20.0,
            }
        )
        cls.env["sale.delivery.carrier.preference"].create(
            {
                "sequence": 20,
                "preference": "carrier",
                "carrier_id": cls.the_poste_carrier.id,
                "sale_order_max_weight": 40.0,
            }
        )
        cls.env["sale.delivery.carrier.preference"].create(
            {"sequence": 30, "preference": "partner", "sale_order_max_weight": 60.0}
        )
        cls.env["sale.delivery.carrier.preference"].create(
            {
                "sequence": 40,
                "preference": "carrier",
                "carrier_id": cls.free_delivery_carrier.id,
                "sale_order_max_weight": 0.0,
            }
        )

    @classmethod
    def _create_sale_order(cls):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 2
        return sale_form.save()

    @classmethod
    def _update_order_line_qty(cls, order, qty):
        with Form(order) as sale_form:
            with sale_form.order_line.edit(0) as line:
                line.product_uom_qty = qty

    def test_available_carriers(self):
        sale_order = self._create_sale_order()
        self.assertAlmostEqual(sale_order.shipping_weight, 20.0)
        carriers = self.env["sale.delivery.carrier.preference"].get_preferred_carriers(
            sale_order
        )
        self.assertEqual(
            carriers,
            self.free_delivery_carrier
            | self.the_poste_carrier
            | self.normal_delivery_carrier
            | self.partner_specific_carrier,
        )
        preferred_carrier = sale_order.get_preferred_carrier()
        self.assertEqual(preferred_carrier, self.normal_delivery_carrier)
        self._update_order_line_qty(sale_order, 3.0)
        self.assertAlmostEqual(sale_order.shipping_weight, 30.0)
        carriers = self.env["sale.delivery.carrier.preference"].get_preferred_carriers(
            sale_order
        )
        self.assertEqual(
            carriers,
            self.free_delivery_carrier
            | self.the_poste_carrier
            | self.partner_specific_carrier,
        )
        preferred_carrier = sale_order.get_preferred_carrier()
        self.assertEqual(preferred_carrier, self.the_poste_carrier)
        self._update_order_line_qty(sale_order, 5.0)
        self.assertAlmostEqual(sale_order.shipping_weight, 50.0)
        carriers = self.env["sale.delivery.carrier.preference"].get_preferred_carriers(
            sale_order
        )
        self.assertEqual(
            carriers, self.free_delivery_carrier | self.partner_specific_carrier
        )
        preferred_carrier = sale_order.get_preferred_carrier()
        self.assertEqual(preferred_carrier, self.partner_specific_carrier)
        self._update_order_line_qty(sale_order, 7.0)
        self.assertAlmostEqual(sale_order.shipping_weight, 70.0)
        carriers = self.env["sale.delivery.carrier.preference"].get_preferred_carriers(
            sale_order
        )
        self.assertEqual(carriers, self.free_delivery_carrier)
        preferred_carrier = sale_order.get_preferred_carrier()
        self.assertEqual(preferred_carrier, self.free_delivery_carrier)
