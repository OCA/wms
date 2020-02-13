from odoo.tests.common import Form

from .common import CommonCase


class ClusterPickingCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.process.picking_type_ids
        cls.main_batch = cls._create_batch_picking(cls.product_a)

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="cluster_picking")

    @classmethod
    def _create_batch_picking(cls, product):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.picking_type
        picking_form.location_id = cls.stock_location
        picking_form.location_dest_id = cls.packing_location
        with picking_form.move_ids_without_package.new() as move:
            move.product_id = product
            move.product_uom_qty = 1
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()

        batch_form = Form(cls.env["stock.picking.batch"])
        batch_form.picking_ids.add(picking)
        return batch_form.save()

    def test_to_openapi(self):
        # will raise if it fails to generate the openapi specs
        self.service.to_openapi()

    # def test_list_manual_batch(self):
    #     """Test getting list of picking batches the user can work on"""
    #     # Simulate the client asking the list of picking batch it can
    #     # select after the user clicked on the "Manual Selection" button
    #     response = self.service.dispatch("/list_manual_selection")
    #     import pdb; pdb.set_trace()
