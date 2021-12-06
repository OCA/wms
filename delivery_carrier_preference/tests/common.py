# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES
from odoo.addons.stock_available_to_promise_release.tests.common import (
    PromiseReleaseCommonCase,
)

PRIORITY_NORMAL = PROCUREMENT_PRIORITIES[0][0]
PRIORITY_URGENT = PROCUREMENT_PRIORITIES[1][0]


class DeliveryCarrierPreferenceCommon(PromiseReleaseCommonCase):
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
                "picking_domain": f"[('priority', '=', '{PRIORITY_URGENT}')]",
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
