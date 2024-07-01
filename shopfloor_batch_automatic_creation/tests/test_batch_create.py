# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# pylint: disable=missing-return

from odoo.addons.shopfloor.tests.common import CommonCase
from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

PRIORITY_NORMAL = PROCUREMENT_PRIORITIES[0][0]
PRIORITY_URGENT = PROCUREMENT_PRIORITIES[1][0]


class TestBatchCreate(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_cluster_picking")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData()
        cls.picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.picking3 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking4 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.pickings = cls.picking1 + cls.picking2 + cls.picking3 + cls.picking4
        cls._fill_stock_for_moves(cls.pickings.move_ids)
        cls.pickings.action_assign()
        cls.device = cls.env["stock.device.type"].create(
            {
                "name": "device",
                "min_volume": 0,
                "max_volume": 1000,
                "max_weight": 1000,
                "nbr_bins": 20,
                "sequence": 1,
            }
        )
        cls.menu.sudo().stock_device_type_ids = cls.device

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "cluster_picking", profile=self.profile, menu=self.menu
        )
        with self.work_on_actions() as work:
            self.auto_batch = work.component(usage="picking.batch.auto.create")

    def test_create_batch(self):
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
        )
        self.assertEqual(batch.picking_ids, self.pickings)

    def test_create_batch_max_pickings(self):
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=6,
        )
        self.assertEqual(
            batch.picking_ids, self.picking1 + self.picking2 + self.picking3
        )

    def test_create_batch_priority(self):
        self.picking2.priority = PRIORITY_URGENT
        self.picking3.priority = PRIORITY_URGENT
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=6,
        )
        # even if we don't reach the max picking, we should not mix the priorities
        # to make delivery of higher priorities faster
        self.assertEqual(batch.picking_ids, self.picking2 + self.picking3)

    def test_create_batch_user(self):
        (self.picking1 + self.picking4).user_id = self.env.ref("base.user_demo")
        (self.picking2 + self.picking3).user_id = self.env.user
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=6,
        )
        # when we have users on pickings, we select only those for the batch
        self.assertEqual(batch.picking_ids, self.picking2 + self.picking3)

    def test_create_batch_max_weight(self):
        # each picking has 2 lines of 10 units, set weight of 1kg per unit,
        # we'll have a total weight of 20kg per picking
        self.product_a.weight = 1
        self.product_b.weight = 1
        # but on the second picking, we set a weight of 2kg per unit: 40 kg per
        # picking
        self.product_c.weight = 2
        self.product_d.weight = 2
        self.pickings.move_ids._cal_move_weight()
        self.pickings._cal_weight()
        # with a max weight of 40, we can take the first picking, but the
        # second one would exceed the max, the third can be added because it's
        # still in the limit
        self.device.max_weight = 40
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
        )
        self.assertEqual(batch.picking_ids, self.picking1 + self.picking3)

    def test_create_batch_max_weight_all_exceed(self):
        """Test batch creation with all pickings exceeding the max weight.

        In such case the batch is anyway created with the first picking in it
        because it's ok to have one picking exceeding the max weight (otherwise
        those pickings will never be processed).
        """
        # each picking has 2 lines of 10 units, set weight of 1kg per unit,
        # we'll have a total weight of 20kg per picking
        self.product_a.weight = 1
        self.product_b.weight = 1
        self.product_c.weight = 1
        self.product_d.weight = 1

        # with a max weight of 10, we can normally take no picking
        self.device.max_weight = 10
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
        )
        self.assertFalse(batch.picking_ids)

    def test_create_batch_max_volume(self):
        # each picking has 2 lines of 10 units, set volume of 0.1m3 per unit,
        # we'll have a total volume of 2m3 per picking
        self.product_a.volume = 0.1
        self.product_b.volume = 0.1
        # but on the second picking, we set a volume of 0.2m3 per unit: 4m3 kg
        # per picking
        self.product_c.volume = 0.2
        self.product_d.volume = 0.2
        self.pickings.move_ids._compute_volume()
        self.pickings._compute_volume()
        # with a max volume of 4, we can take the first picking, but the
        # second one would exceed the max, the third can be added because it's
        # still in the limit
        self.device.max_volume = 4
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
        )
        self.assertEqual(batch.picking_ids, self.picking1 + self.picking3)

    def test_create_batch_max_volume_all_exceed(self):
        """Test batch creation with all pickings exceeding the max volume.

        In such case the batch is anyway created with the first picking in it
        because it's ok to have one picking exceeding the max volume (otherwise
        those pickings will never be processed).
        """
        # each picking has 2 lines of 10 units, set volume of 0.1m3 per unit,
        # we'll have a total volume of 2m3 per picking
        self.product_a.volume = 0.1
        self.product_b.volume = 0.1
        self.product_c.volume = 0.1
        self.product_d.volume = 0.1
        self.pickings.move_ids._compute_volume()
        self.pickings._compute_volume()
        # with a max volume of 1, we can normally take no picking
        self.device.max_volume = 1
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
        )
        self.assertFalse(batch.picking_ids)

    def test_cluster_picking_select(self):
        self.menu.sudo().batch_create = True

        response = self.service.dispatch("find_batch")
        batch = self.picking1.batch_id
        self.assertEqual(batch.user_id, self.env.user)
        self.assertEqual(batch.state, "in_progress")

        data = self.data.picking_batch(batch, with_pickings=True)
        self.assert_response(
            response,
            next_state="confirm_start",
            data=data,
        )

    def test_create_batch_group_by_commercial_partner(self):
        """Test batch creation by grouping all operations of the same
        commercial entity, ignoring priorities and limits.
        """
        partner_model = self.env["res.partner"].sudo()
        partner1_com = partner_model.create(
            {"name": "COM PARTNER 1", "is_company": True}
        )
        partner1_contact = partner_model.create(
            {
                "name": "CONTACT PARTNER 1",
                "parent_id": partner1_com.id,
                "is_company": False,
            }
        )
        partner2_com = partner_model.create(
            {"name": "COM PARTNER 2", "is_company": True}
        )
        partner2_contact = partner_model.create(
            {
                "name": "CONTACT PARTNER 2",
                "parent_id": partner2_com.id,
                "is_company": False,
            }
        )
        self.picking1.write({"partner_id": partner1_contact.id})
        self.picking2.write({"partner_id": partner2_contact.id})
        self.picking3.write({"partner_id": partner2_contact.id})
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
            group_by_commercial_partner=True,
        )
        self.assertEqual(batch.picking_ids, self.picking1)
        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
            group_by_commercial_partner=True,
        )
        self.assertEqual(batch.picking_ids, self.picking2 | self.picking3)

    def test_specific_device_sort_key(self):
        self.device.sudo().line_sort_key_code = "key=line.product_id.weight"
        self.product_a.weight = 1
        self.product_b.weight = 5
        self.product_c.weight = 15
        self.product_d.weight = 20

        batch = self.auto_batch.create_batch(
            self.picking_type,
            stock_device_types=self.device,
            maximum_number_of_preparation_lines=20,
        )
        lines = batch.move_line_ids
        lines = self.service._lines_for_picking_batch(batch)
        self.assertEqual(
            lines.mapped("product_id"),
            self.product_a + self.product_b + self.product_c + self.product_d,
        )
        self.product_a.weight = 25
        lines = self.service._lines_for_picking_batch(batch)
        self.assertEqual(
            lines.mapped("product_id"),
            self.product_b + self.product_c + self.product_d + self.product_a,
        )
        # we can call super method to use the default sorting
        self.device.sudo().line_sort_key_code = (
            "key=(line.product_id.weight,) + super(line)"
        )
        lines = self.service._lines_for_picking_batch(batch)
        self.assertEqual(
            lines.mapped("product_id"),
            self.product_b + self.product_c + self.product_d + self.product_a,
        )
