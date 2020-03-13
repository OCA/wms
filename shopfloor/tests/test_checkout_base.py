from odoo.tests.common import Form

from .common import CommonCase


class CheckoutCommonCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_checkout")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.wh.delivery_steps = "pick_pack_ship"
        cls.picking_type = cls.process.picking_type_id

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="checkout")

    def _create_picking(self, picking_type=None):
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = picking_type or self.picking_type
        picking_form.partner_id = self.customer
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_a
            move.product_uom_qty = 10
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_b
            move.product_uom_qty = 10
        picking = picking_form.save()
        picking.action_confirm()
        return picking

    def _stock_picking_data(self, picking):
        return self.service._data_for_stock_picking(picking)


class CheckoutOpenAPICase(CheckoutCommonCase):
    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()
