# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .model_common import ModelCommon

# pylint: disable=missing-return


class TestStockSplit(ModelCommon):
    @classmethod
    def setUpClassData(cls):
        super().setUpClassData()
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
                "state": "waiting",
            }
        )
        cls.pack_move_a = cls.env["stock.move"].create(
            {
                "name": cls.product_a.display_name,
                "product_id": cls.product_a.id,
                "product_uom_qty": 15.0,
                "product_uom": cls.product_a.uom_id.id,
                "location_id": cls.pack_location.id,
                "location_dest_id": cls.ship_location.id,
                "warehouse_id": cls.warehouse.id,
                "picking_type_id": cls.warehouse.pack_type_id.id,
                "procure_method": "make_to_order",
                "state": "waiting",
                "move_dest_ids": [(4, cls.ship_move_a.id)],
            }
        )
        cls.pick_move_a = cls.env["stock.move"].create(
            {
                "name": cls.product_a.display_name,
                "product_id": cls.product_a.id,
                "product_uom_qty": 15.0,
                "product_uom": cls.product_a.uom_id.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.pack_location.id,
                "warehouse_id": cls.warehouse.id,
                "picking_type_id": cls.warehouse.pick_type_id.id,
                "procure_method": "make_to_stock",
                "state": "confirmed",
                "move_dest_ids": [(4, cls.pack_move_a.id)],
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
                "state": "waiting",
            }
        )
        cls.pack_move_b = cls.env["stock.move"].create(
            {
                "name": cls.product_b.display_name,
                "product_id": cls.product_b.id,
                "product_uom_qty": 4.0,
                "product_uom": cls.product_b.uom_id.id,
                "location_id": cls.pack_location.id,
                "location_dest_id": cls.ship_location.id,
                "warehouse_id": cls.warehouse.id,
                "picking_type_id": cls.warehouse.pack_type_id.id,
                "procure_method": "make_to_order",
                "state": "waiting",
                "move_dest_ids": [(4, cls.ship_move_b.id)],
            }
        )
        cls.pick_move_b = cls.env["stock.move"].create(
            {
                "name": cls.product_b.display_name,
                "product_id": cls.product_b.id,
                "product_uom_qty": 4.0,
                "product_uom": cls.product_b.uom_id.id,
                "location_id": cls.stock_location.id,
                "location_dest_id": cls.pack_location.id,
                "warehouse_id": cls.warehouse.id,
                "picking_type_id": cls.warehouse.pick_type_id.id,
                "procure_method": "make_to_stock",
                "state": "confirmed",
                "move_dest_ids": [(4, cls.pack_move_b.id)],
            }
        )
        (
            cls.ship_move_a
            | cls.ship_move_b
            | cls.pack_move_a
            | cls.pack_move_b
            | cls.pick_move_a
            | cls.pick_move_b
        )._assign_picking()
        cls.picking = cls.pick_move_a.picking_id
        cls.packing = cls.pack_move_a.picking_id
        cls.picking.action_assign()

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
            move_line.qty_done = move_line.reserved_uom_qty
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
        move_lines_to_process._extract_in_split_order()
        new_packing = self.packing.backorder_ids
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
            move_line.qty_done = move_line.reserved_uom_qty
        self.pick_move_b.extract_and_action_done()
        new_picking = self.picking.backorder_ids
        self.assertTrue(new_picking)
        # Check move lines repartition
        self.assertNotIn(self.pick_move_b, self.picking.move_ids)
        self.assertEqual(new_picking.move_ids, self.pick_move_b)
        # Check states
        self.assertEqual(self.picking.state, "assigned")
        self.assertEqual(self.pick_move_b.state, "done")
        self.assertEqual(new_picking.state, "done")

    def test_extract_and_action_done_multiple_assigned_moves(self):
        self.assertFalse(self.picking.backorder_ids)
        self.assertEqual(self.picking.state, "assigned")
        for move_line in self.picking.move_line_ids:
            move_line.qty_done = move_line.reserved_uom_qty
        self.picking.move_ids.extract_and_action_done()
        # No backorder as all moves of the picking have been validated
        new_picking = self.picking.backorder_ids
        self.assertFalse(new_picking)
        # Check move lines repartition
        self.assertEqual(len(self.picking.move_ids), 2)
        # Check states
        self.assertEqual(self.picking.state, "done")
