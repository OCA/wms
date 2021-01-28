# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests import tagged
from odoo.tests.common import SavepointCase


@tagged("post_install", "-at_install")
class TestStockSplit(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestStockSplit, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.delivery_steps = "pick_pack_ship"
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.pack_location = cls.warehouse.wh_pack_stock_loc_id
        cls.ship_location = cls.warehouse.wh_output_stock_loc_id
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        # Create products
        cls.product_a = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product A",
                    "type": "product",
                    "default_code": "A",
                    "barcode": "A",
                    "weight": 2,
                }
            )
        )
        cls.product_a_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_a.id,
                    "barcode": "ProductABox",
                }
            )
        )
        cls.product_b = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product B",
                    "type": "product",
                    "default_code": "B",
                    "barcode": "B",
                    "weight": 2,
                }
            )
        )
        cls.product_b_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_b.id,
                    "barcode": "ProductBBox",
                }
            )
        )
        # Put product_a quantities in different packages to get several move lines
        cls.package_1 = cls.env["stock.quant.package"].create({"name": "PACKAGE_1"})
        cls.package_2 = cls.env["stock.quant.package"].create({"name": "PACKAGE_2"})
        cls.package_3 = cls.env["stock.quant.package"].create({"name": "PACKAGE_3"})
        cls.package_4 = cls.env["stock.quant.package"].create({"name": "PACKAGE_4"})
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 6, package=cls.package_1
        )
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 4, package=cls.package_2
        )
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 5, package=cls.package_3
        )
        # Put product_b quantities in stock
        cls._update_qty_in_location(cls.stock_location, cls.product_b, 10)
        # Create the pick/pack/ship transfer
        cls.ship_move_a = cls.env["stock.move"].create(
            {
                "name": cls.product_a.display_name,
                "product_id": cls.product_a.id,
                "product_uom_qty": 15.0,
                "product_uom": cls.product_a.uom_id.id,
                "location_id": cls.ship_location.id,
                "location_dest_id": cls.customer_location.id,
                "warehouse_id": cls.warehouse.id,
                "picking_type_id": cls.warehouse.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        cls.ship_move_b = cls.env["stock.move"].create(
            {
                "name": cls.product_b.display_name,
                "product_id": cls.product_b.id,
                "product_uom_qty": 4,
                "product_uom": cls.product_b.uom_id.id,
                "location_id": cls.ship_location.id,
                "location_dest_id": cls.customer_location.id,
                "warehouse_id": cls.warehouse.id,
                "picking_type_id": cls.warehouse.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        (cls.ship_move_a | cls.ship_move_b)._assign_picking()
        (cls.ship_move_a | cls.ship_move_b)._action_confirm(merge=False)
        cls.pack_move_a = cls.ship_move_a.move_orig_ids[0]
        cls.pick_move_a = cls.pack_move_a.move_orig_ids[0]
        cls.pack_move_b = cls.ship_move_b.move_orig_ids[0]
        cls.pick_move_b = cls.pack_move_b.move_orig_ids[0]
        cls.picking = cls.pick_move_a.picking_id
        cls.packing = cls.pack_move_a.picking_id
        cls.picking.action_assign()

    @classmethod
    def _update_qty_in_location(
        cls, location, product, quantity, package=None, lot=None
    ):
        quants = cls.env["stock.quant"]._gather(
            product, location, lot_id=lot, package_id=package, strict=True
        )
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(
            product, location, quantity, package_id=package, lot_id=lot
        )

    def test_split_pickings_from_source_location(self):
        dest_location = self.pick_move_a.location_dest_id.sudo().copy(
            {
                "name": self.pick_move_a.location_dest_id.name + "_2",
                "barcode": self.pick_move_a.location_dest_id.barcode + "_2",
                "location_id": self.pick_move_a.location_dest_id.id,
            }
        )
        # Pick goods from stock and move some of them to a different destination
        self.assertEqual(self.pick_move_a.state, "assigned")
        for i, move_line in enumerate(self.pick_move_a.move_line_ids):
            move_line.qty_done = move_line.product_uom_qty
            if i % 2:
                move_line.location_dest_id = dest_location
        self.pick_move_a.extract_and_action_done()
        self.assertEqual(self.pick_move_a.state, "done")
        # Pack step, we want to split move lines from common source location
        self.assertEqual(self.pack_move_a.state, "assigned")
        move_lines_to_process = self.pack_move_a.move_line_ids.filtered(
            lambda ml: ml.location_id == dest_location
        )
        self.assertEqual(len(self.pack_move_a.move_line_ids), 3)
        self.assertEqual(len(self.packing.package_level_ids), 3)
        self.assertEqual(len(move_lines_to_process), 1)
        new_packing = move_lines_to_process._split_pickings_from_source_location()
        self.assertEqual(len(self.packing.package_level_ids), 2)
        self.assertEqual(len(new_packing.package_level_ids), 1)
        self.assertEqual(len(new_packing.move_line_ids), 1)
        self.assertTrue(new_packing != self.packing)
        self.assertEqual(new_packing.backorder_id, self.packing)
        self.assertEqual(
            self.pick_move_a.move_dest_ids.picking_id, self.packing | new_packing
        )
        self.assertEqual(move_lines_to_process.state, "assigned")
        self.assertEqual(
            set(self.pack_move_a.move_line_ids.mapped("state")), {"assigned"}
        )

    def test_extract_and_action_done_one_assigned_move(self):
        self.assertFalse(self.picking.backorder_ids)
        self.assertEqual(self.picking.state, "assigned")
        for move_line in self.pick_move_b.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        self.pick_move_b.extract_and_action_done()
        new_picking = self.picking.backorder_ids
        self.assertTrue(new_picking)
        # Check move lines repartition
        self.assertNotIn(self.pick_move_b, self.picking.move_lines)
        self.assertEqual(new_picking.move_lines, self.pick_move_b)
        # Check states
        self.assertEqual(self.picking.state, "assigned")
        self.assertEqual(self.pick_move_b.state, "done")
        self.assertEqual(new_picking.state, "done")

    def test_extract_and_action_done_multiple_assigned_moves(self):
        self.assertFalse(self.picking.backorder_ids)
        self.assertEqual(self.picking.state, "assigned")
        for move_line in self.picking.move_line_ids:
            move_line.qty_done = move_line.product_uom_qty
        self.picking.move_lines.extract_and_action_done()
        # No backorder as all moves of the picking have been validated
        new_picking = self.picking.backorder_ids
        self.assertFalse(new_picking)
        # Check move lines repartition
        self.assertEqual(len(self.picking.move_lines), 2)
        # Check states
        self.assertEqual(self.picking.state, "done")
