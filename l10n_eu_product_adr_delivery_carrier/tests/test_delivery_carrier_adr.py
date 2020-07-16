# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests import Form, SavepointCase


class TestDeliveryCarrierDangerousGoods(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env.ref("base.res_partner_2")
        cls.product = cls.env.ref("product.product_product_9")
        cls.dangerous_limited_amount = cls.env.ref(
            "l10n_eu_product_adr.limited_amount_2"
        )
        cls.the_poste_carrier = cls.env.ref("delivery.delivery_carrier")
        cls.free_delivery_carrier = cls.env.ref("delivery.free_delivery_carrier")
        cls.the_poste_carrier.write(
            {"adr_limited_amount_ids": [(4, cls.dangerous_limited_amount.id)]}
        )
        cls.product.limited_amount_id = cls.dangerous_limited_amount.id

    def test_picking_warning(self):
        delivery_order_type = self.env.ref("stock.picking_type_out")
        stock_picking_form = Form(
            self.env["stock.picking"].with_context(
                {"default_picking_type_id": delivery_order_type.id}
            )
        )
        stock_picking_form.partner_id = self.partner
        with stock_picking_form.move_ids_without_package.new() as move_form:
            move_form.product_id = self.product
        stock_picking_form.carrier_id = self.free_delivery_carrier

    def test_sale_order_warning(self):
        sale_order_form = Form(self.env["sale.order"])
        sale_order_form.partner_id = self.partner
        with sale_order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        sale_order = sale_order_form.save()
        add_shipping_wiz_form = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale_order.id}
            )
        )
        self.assertNotEqual(add_shipping_wiz_form.carrier_id, self.the_poste_carrier)
        self.assertFalse(add_shipping_wiz_form.dangerous_goods_message)
        add_shipping_wiz_form.carrier_id = self.the_poste_carrier
        self.assertTrue(add_shipping_wiz_form.dangerous_goods_message)
