# Copyright 2021 <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)

from odoo.tests import SavepointCase


class TestStockPreLocationPutaway(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        ref = cls.env.ref
        cls.warehouse = ref("stock.warehouse0")
        # set two steps reception on warehouse
        cls.warehouse.reception_steps = "two_steps"

        cls.suppliers_location = ref("stock.stock_location_suppliers")
        cls.input_location = ref("stock.stock_location_company")
        cls.stock_location = ref("stock.stock_location_stock")

        # create some stock sub locations
        cls.stock_a = ref("stock_prelocation_putaway.stock_location_a")
        cls.stock_a_1 = ref("stock_prelocation_putaway.stock_location_a_1")
        cls.stock_a_1_alpha = ref("stock_prelocation_putaway.stock_location_a_1_alpha")
        cls.stock_a_1_beta = ref("stock_prelocation_putaway.stock_location_a_1_beta")
        cls.stock_a_2 = ref("stock_prelocation_putaway.stock_location_a_2")
        cls.stock_b = ref("stock_prelocation_putaway.stock_location_b")
        cls.stock_b_1 = ref("stock_prelocation_putaway.stock_location_b_1")
        cls.stock_g = ref("stock_prelocation_putaway.stock_location_g")
        cls.stock_g_1 = ref("stock_prelocation_putaway.stock_location_g_1")

        # create some input sub locations
        cls.input_a = ref("stock_prelocation_putaway.stock_location_input_a")
        cls.input_a_1 = ref("stock_prelocation_putaway.stock_location_input_a_1")
        cls.input_b_to_g = ref("stock_prelocation_putaway.stock_location_input_b_to_g")
        cls.receipts_picking_type = ref("stock.picking_type_in")
        cls.internal_picking_type = ref("stock.picking_type_internal")

        cls.product1 = cls.env["product.product"].create(
            {"name": "Product 1", "type": "product"}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Product 2", "type": "product"}
        )
        cls.product3 = cls.env["product.product"].create(
            {"name": "Product 3", "type": "product"}
        )
        cls.product4 = cls.env["product.product"].create(
            {"name": "Product 4", "type": "product"}
        )
        cls.product5 = cls.env["product.product"].create(
            {"name": "Product 5", "type": "product"}
        )

        cls.internal_picking_type.write({"show_entire_packs": True})
        # show_reserved must be set here because it changes the behaviour of
        # put_in_pack operation:
        # if show_reserved: qty_done must be set on stock.picking.move_line_ids
        # if not show_reserved: qty_done must be set on
        # stock.picking.move_line_nosuggest_ids
        cls.receipts_picking_type.write(
            {"show_entire_packs": True, "show_reserved": True}
        )

    def _create_putway(self):
        self.putaway_p1a1beta = self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product1.id,
                "location_in_id": self.stock_location.id,
                "location_out_id": self.stock_a_1_beta.id,
            }
        )
        self.putaway_p2a2 = self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product2.id,
                "location_in_id": self.stock_location.id,
                "location_out_id": self.stock_a_2.id,
            }
        )
        self.putaway_p3b1 = self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product3.id,
                "location_in_id": self.stock_location.id,
                "location_out_id": self.stock_b_1.id,
            }
        )
        self.putaway_p4g = self.env["stock.putaway.rule"].create(
            {
                "product_id": self.product4.id,
                "location_in_id": self.stock_location.id,
                "location_out_id": self.stock_g.id,
            }
        )
        # no putaway for 5
        self.putaways = [
            self.putaway_p4g,
            self.putaway_p3b1,
            self.putaway_p2a2,
            self.putaway_p1a1beta,
        ]

        self.stock_a.pre_location_ids = self.input_a
        self.stock_b.pre_location_ids = self.input_b_to_g
        self.stock_g.pre_location_ids = self.input_b_to_g

        self.expected_product_mapping = {
            self.product1.id: (self.input_a.id, self.stock_a_1_beta.id),
            self.product2.id: (self.input_a.id, self.stock_a_2.id),
            self.product3.id: (self.input_b_to_g.id, self.stock_b_1.id),
            self.product4.id: (self.input_b_to_g.id, self.stock_g.id),
            self.product5.id: (self.input_location.id, self.stock_location.id),
        }

    def _create_picking_in(self):
        """Create input picking"""

        move_lines = [
            (
                0,
                0,
                {
                    "name": product.name,
                    "product_id": product.id,
                    "product_uom_qty": 4,
                    "product_uom": product.uom_id.id,
                },
            )
            for product in [
                self.product1,
                self.product2,
                self.product3,
                self.product4,
                self.product5,  # no putaway
                self.product2,  # twice
            ]
        ]

        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_lines": move_lines,
            }
        )
        # Mark as todo
        in_picking.action_confirm()

        # set quantities
        for ml in in_picking.move_line_ids:
            ml.qty_done = ml.product_uom_qty

        self.in_picking_1 = in_picking

    def test_pre_putaway(self):
        """ Test a simple case with different depths"""
        self._create_putway()
        self._create_picking_in()

        # ensure 2 pickings
        self.in_picking_2 = self.in_picking_1.move_lines.mapped("move_dest_ids").mapped(
            "picking_id"
        )
        self.assertTrue(self.in_picking_2.exists())

        # validate picking 1
        self.in_picking_1.button_validate()

        # validate state of picking 2
        self.assertEqual(self.in_picking_2.state, "assigned")

        # check mapping of picking2
        mapping = {}
        for ml in self.in_picking_2.move_line_ids:
            mapping[ml.product_id.id] = (ml.location_id.id, ml.location_dest_id.id)

        expected_mapping = {}
        for ml in self.in_picking_2.move_line_ids:
            expected_mapping[ml.product_id.id] = self.expected_product_mapping[
                ml.product_id.id
            ]
        self.assertDictEqual(mapping, expected_mapping)

    def test_get_pre_location(self):
        self.stock_a.pre_location_ids = self.input_a

        self.assertEqual(
            self.stock_a_1_alpha._get_pre_location(self.input_location), self.input_a
        )
        self.assertEqual(
            self.stock_a_1_beta._get_pre_location(self.input_location), self.input_a
        )
        self.assertEqual(
            self.stock_a_1._get_pre_location(self.input_location), self.input_a
        )
        self.assertEqual(
            self.stock_a_2._get_pre_location(self.input_location), self.input_a
        )

        self.stock_b.pre_location_ids = self.input_b_to_g

        self.assertEqual(
            self.stock_b._get_pre_location(self.input_location), self.input_b_to_g
        )
        self.assertEqual(
            self.stock_b_1._get_pre_location(self.input_location), self.input_b_to_g
        )

    def test_get_pre_location_depth(self):
        # test with more input depth
        self.stock_a.pre_location_ids = self.input_a_1

        self.assertEqual(
            self.stock_a_1_alpha._get_pre_location(self.input_location), self.input_a_1
        )
        self.assertEqual(
            self.stock_a_1._get_pre_location(self.input_location), self.input_a_1
        )
