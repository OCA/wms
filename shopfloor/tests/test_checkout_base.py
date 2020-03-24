from odoo.tests.common import Form

from .common import CommonCase


class CheckoutCommonCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product", "barcode": "product_a"}
        )
        cls.product_a_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_a.id, "barcode": "ProductABox"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "type": "product", "barcode": "product_b"}
        )
        cls.product_b_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_b.id, "barcode": "ProductBBox"}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "Product C", "type": "product", "barcode": "product_c"}
        )
        cls.product_c_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_b.id, "barcode": "ProductCBox"}
        )
        cls.product_d = cls.env["product.product"].create(
            {"name": "Product D", "type": "product", "barcode": "product_d"}
        )
        cls.product_d_packaging = cls.env["product.packaging"].create(
            {"name": "Box", "product_id": cls.product_d.id, "barcode": "ProductDBox"}
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

    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = picking_type or cls.picking_type
        picking_form.partner_id = cls.customer
        if lines is None:
            lines = [(cls.product_a, 10), (cls.product_b, 10)]
        for product, qty in lines:
            with picking_form.move_ids_without_package.new() as move:
                move.product_id = product
                move.product_uom_qty = qty
        picking = picking_form.save()
        if confirm:
            picking.action_confirm()
        return picking

    def _stock_picking_data(self, picking):
        return self.service._data_for_stock_picking(picking)

    def _move_line_data(self, move_line):
        return self.service._data_for_move_line(move_line)
