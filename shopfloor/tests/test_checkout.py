from odoo.tests.common import Form

from .common import CommonCase


class CheckoutCase(CommonCase):
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

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()

    def _create_picking(self):
        picking_form = Form(self.env["stock.picking"])
        picking_form.picking_type_id = self.picking_type
        # TODO we must have packages in origin
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = self.product_a
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        return picking

    def _stock_picking_data(self, picking):
        return self.service._data_for_stock_picking(picking)

    def test_scan_document_stock_picking_ok(self):
        picking = self._create_picking()
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        response = self.service.dispatch(
            "scan_document", params={"barcode": picking.name}
        )
        self.assert_response(
            response, next_state="select_line", data=self._stock_picking_data(picking)
        )
