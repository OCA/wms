from odoo.tests.common import Form

from .common import CommonCase


class BatchPickingCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product A", "type": "product"}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product B", "type": "product"}
        )
        # which menu we pick should not matter for the batch picking api
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_cluster_picking")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.process.picking_type_id
        cls.batch1 = cls._create_picking_batch(cls.product_a)
        cls.batch2 = cls._create_picking_batch(cls.product_a)
        cls.batch3 = cls._create_picking_batch(cls.product_a)
        cls.batch4 = cls._create_picking_batch(cls.product_b)
        cls.batch5 = cls._create_picking_batch(cls.product_b)
        cls.batch6 = cls._create_picking_batch(cls.product_b)
        cls.all_batches = (
            cls.batch1 + cls.batch2 + cls.batch3 + cls.batch4 + cls.batch5 + cls.batch6
        )

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="picking_batch")

    @classmethod
    def _create_picking_batch(cls, product):
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

    def test_search_empty(self):
        """No batch is available"""
        # Simulate the client asking the list of picking batch
        response = self.service.dispatch("search")
        # none of the pickings are assigned, so we can't work on them
        self.assert_response(response, data={"size": 0, "records": []})

    def test_search(self):
        """Return only draft batches with assigned pickings """
        pickings = self.all_batches.mapped("picking_ids")
        self._fill_stock_for_pickings(pickings)
        pickings.action_assign()
        self.assertTrue(all(p.state == "assigned" for p in pickings))
        # we should not have done batches in list
        self.batch5.state = "done"
        # nor canceled batches
        self.batch6.state = "cancel"
        # we should not have batches in progress
        self.batch4.user_id = self.env.ref("base.user_demo")
        self.batch4.confirm_picking()
        # unless it's assigned to our user
        self.batch3.user_id = self.env.user
        self.batch3.confirm_picking()

        # Simulate the client asking the list of picking batch
        response = self.service.dispatch("search")
        self.assert_response(
            response,
            data={
                "size": 3,
                "records": [
                    {
                        "id": self.batch1.id,
                        "name": self.batch1.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                    },
                    {
                        "id": self.batch2.id,
                        "name": self.batch2.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                    },
                    {
                        "id": self.batch3.id,
                        "name": self.batch3.name,
                        "picking_count": 1,
                        "move_line_count": 1,
                    },
                ],
            },
        )
