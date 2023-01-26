# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
        cls._fill_stock_for_moves(cls.pickings.move_lines)
        cls.pickings.action_assign()

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "cluster_picking", profile=self.profile, menu=self.menu
        )
        with self.work_on_actions() as work:
            self.auto_batch = work.component(usage="picking.batch.auto.create")

    def test_create_batch(self):
        batch = self.auto_batch.create_batch(self.picking_type)
        self.assertEqual(batch.picking_ids, self.pickings)

    def test_create_batch_max_pickings(self):
        batch = self.auto_batch.create_batch(self.picking_type, max_pickings=3)
        self.assertEqual(
            batch.picking_ids, self.picking1 + self.picking2 + self.picking3
        )

    def test_create_batch_priority(self):
        self.picking2.priority = PRIORITY_URGENT
        self.picking3.priority = PRIORITY_URGENT
        batch = self.auto_batch.create_batch(self.picking_type, max_pickings=3)
        # even if we don't reach the max picking, we should not mix the priorities
        # to make delivery of higher priorities faster
        self.assertEqual(batch.picking_ids, self.picking2 + self.picking3)

    def test_create_batch_user(self):
        (self.picking1 + self.picking4).user_id = False
        (self.picking2 + self.picking3).user_id = self.env.user
        batch = self.auto_batch.create_batch(self.picking_type, max_pickings=3)
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

        # with a max weight of 40, we can take the first picking, but the
        # second one would exceed the max, the third can be added because it's
        # still in the limit
        batch = self.auto_batch.create_batch(self.picking_type, max_weight=40)
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

        # with a max weight of 10, we can normally take no picking, but as we
        # need to process them we take at least the first one.
        batch = self.auto_batch.create_batch(self.picking_type, max_weight=10)
        self.assertEqual(batch.picking_ids, self.picking1)

    def test_create_batch_max_volume(self):
        # each picking has 2 lines of 10 units, set volume of 0.1m3 per unit,
        # we'll have a total volume of 2m3 per picking
        self.product_a.volume = 0.1
        self.product_b.volume = 0.1
        # but on the second picking, we set a volume of 0.2m3 per unit: 4m3 kg
        # per picking
        self.product_c.volume = 0.2
        self.product_d.volume = 0.2

        # with a max volume of 4, we can take the first picking, but the
        # second one would exceed the max, the third can be added because it's
        # still in the limit
        batch = self.auto_batch.create_batch(self.picking_type, max_volume=4)
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

        # with a max volume of 1, we can normally take no picking, but as we
        # need to process them we take at least the first one.
        batch = self.auto_batch.create_batch(self.picking_type, max_volume=1)
        self.assertEqual(batch.picking_ids, self.picking1)

    def test_volume(self):
        # varying volumes because of the packing
        volume_1 = 0.1
        volume_2 = 0.25
        volume_4 = 0.6
        self.product_a.volume = 0.1
        cm_uom = self.env.ref("uom.product_uom_cm")
        self.env["product.packaging"].sudo().create(
            {
                "name": "pair",
                "product_id": self.product_a.id,
                "qty": 2,
                "height": 100,
                "width": 100,
                "packaging_length": volume_2 * 100,
                "length_uom_id": cm_uom.id,
            }
        )
        self.env["product.packaging"].sudo().create(
            {
                "name": "double pairs",
                "product_id": self.product_a.id,
                "qty": 4,
                "height": 100,
                "width": 100,
                "packaging_length": volume_4 * 100,
                "length_uom_id": cm_uom.id,
            }
        )
        # fmt: off
        quantity = (
            1  # unit,
            + 1 * 2  # 1 * pair
            + 5 * 4  # 5 * double pairs
        )
        expected_volume = (
            1 * volume_1
            + 1 * volume_2
            + 5 * volume_4
        )
        # fmt: on
        picking = self._create_picking(lines=[(self.product_a, quantity)])
        volume = self.auto_batch._picking_volume(picking)
        self.assertEqual(volume, expected_volume)

    def test_cluster_picking_select(self):
        self.menu.sudo().batch_create = True
        self.menu.sudo().batch_create_max_picking = 2

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
        self.picking1.write(
            {"priority": PRIORITY_NORMAL, "partner_id": partner1_contact.id}
        )
        self.picking2.write(
            {"priority": PRIORITY_NORMAL, "partner_id": partner2_contact.id}
        )
        self.picking3.write(
            {"priority": PRIORITY_URGENT, "partner_id": partner2_contact.id}
        )
        batch = self.auto_batch.create_batch(
            self.picking_type, group_by_commercial_partner=True
        )
        self.assertEqual(batch.picking_ids, self.picking2 | self.picking3)

    def test_create_batch_only_one_picking_type(self):
        # Test that the created batches only include pickings of the same picking type.
        additional_picking_type = (
            self.env["stock.picking.type"]
            .sudo()
            .create(
                {
                    "code": "internal",
                    "name": "Cluster Picking 2",
                    "sequence_id": 10,
                    "sequence_code": "CPI",
                    "warehouse_id": self.env.ref("stock.warehouse0").id,
                    "default_location_src_id": self.env.ref(
                        "stock.stock_location_stock"
                    ).id,
                    "default_location_dest_id": self.env.ref(
                        "stock.location_pack_zone"
                    ).id,
                }
            )
        )
        picking_types = self.picking_type | additional_picking_type
        additional_picking = self._create_picking(
            picking_type=additional_picking_type,
            lines=[(self.product_a, 10), (self.product_b, 10)],
        )
        additional_picking.action_assign()
        batch = self.auto_batch.create_batch(picking_types)
        self.assertEqual(batch.picking_ids.picking_type_id, self.picking_type)
