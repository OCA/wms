# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form, TransactionCase


class TestSaleDeliveryCarrierPreference(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        ref = cls.env.ref
        cls.partner = ref("base.res_partner_12")
        cls.product = ref("product.product_product_20")
        cls.free_delivery_carrier = ref("delivery.free_delivery_carrier")
        cls.delivery_local_delivery = ref("delivery.delivery_local_delivery")
        cls.warehouse = ref("stock.warehouse0")
        cls.warehouse.delivery_carrier_id = cls.free_delivery_carrier

    @classmethod
    def _create_sale_order(cls):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with sale_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.product_uom_qty = 2
        return sale_form.save()

    def test_warehouse_carrier(self):
        order = self._create_sale_order()
        self.assertEqual(
            self.partner.property_delivery_carrier_id, self.delivery_local_delivery
        )
        action = order.action_open_delivery_wizard()
        default_carrier_id = action["context"]["default_carrier_id"]
        self.assertEqual(default_carrier_id, self.delivery_local_delivery.id)
        self.partner.property_delivery_carrier_id = False
        action = order.action_open_delivery_wizard()
        default_carrier_id = action["context"]["default_carrier_id"]
        self.assertEqual(default_carrier_id, self.free_delivery_carrier.id)
