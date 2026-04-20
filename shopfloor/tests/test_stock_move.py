# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .model_common import ModelCommon


class TestStockMove(ModelCommon):
    @classmethod
    def setUpClassData(cls):
        res = super().setUpClassData()
        cls.picking_type = cls.env.ref("stock.picking_type_internal")
        cls.customer = cls.env["res.partner"].create({"name": "Bob"})
        return res

    def test_extract_in_split_order_partial(self):
        package = self.package_1
        # multiple moves in the same package, one move split, package stays
        self._update_qty_in_location(
            self.stock_location, self.product_a, 10.0, package=package
        )
        self._update_qty_in_location(
            self.stock_location, self.product_b, 10.0, package=package
        )
        picking = self._create_picking(confirm=True)
        move1 = picking.move_ids[0]
        move2 = picking.move_ids[1]
        move_line1 = move1.move_line_ids
        move_line2 = move2.move_line_ids
        package_level = picking.package_level_ids
        self.assertEqual(len(package_level), 1)
        self.assertEqual(package_level, move_line1.package_level_id)
        self.assertEqual(package_level, move_line2.package_level_id)
        split_picking = move2._extract_in_split_order()
        # extracting move2 is taking half the content of the package.
        # Package level remains on picking.
        self.assertEqual(picking.package_level_ids, package_level)
        self.assertEqual(move_line1.package_level_id, package_level)
        self.assertEqual(move_line1.result_package_id, package)
        # move2 has been extracted in a new picking,
        # which shouldn't have a package level
        self.assertFalse(split_picking.package_level_ids)
        self.assertFalse(move_line2.package_level_id)
        self.assertFalse(move_line2.result_package_id)

    def test_extract_in_split_order_full(self):
        package = self.package_1
        # multiple moves in the same package, one move split, package stays
        self._update_qty_in_location(
            self.stock_location,
            self.product_a,
            10.0,
        )
        self._update_qty_in_location(
            self.stock_location, self.product_b, 10.0, package=package
        )
        picking = self._create_picking(confirm=True)
        move1 = picking.move_ids[0]
        move2 = picking.move_ids[1]  # productb
        move_line1 = move1.move_line_ids
        move_line2 = move2.move_line_ids
        package_level = picking.package_level_ids
        self.assertEqual(len(package_level), 1)
        self.assertFalse(move_line1.package_level_id)
        self.assertEqual(package_level, move_line2.package_level_id)
        split_picking = move2._extract_in_split_order()
        # extracting move2 is taking the full package.
        # Package level is moved in the new picking
        self.assertFalse(picking.package_level_ids)
        self.assertFalse(move_line1.package_level_id)
        self.assertFalse(move_line1.result_package_id)
        # move2 has been extracted in a new picking, and the package with it
        self.assertEqual(split_picking.package_level_ids, package_level)
        self.assertEqual(move_line2.package_level_id, package_level)
        self.assertEqual(move_line2.result_package_id, package)

    def test_last_move_from_package_level(self):
        package = self.package_1
        # multiple moves in the same package, one move split, package stays
        self._update_qty_in_location(
            self.stock_location, self.product_a, 10.0, package=package
        )
        self._update_qty_in_location(
            self.stock_location, self.product_b, 10.0, package=package
        )
        picking = self._create_picking(confirm=True)
        move1 = picking.move_ids[0]
        move2 = picking.move_ids[1]
        # Both move1 and move2 are in the package level, so either of them are the last
        self.assertFalse(move1._last_move_from_package_level())
        self.assertFalse(move2._last_move_from_package_level())
        # But together, they represent the last moves of the package level
        self.assertTrue((move1 | move2)._last_move_from_package_level())
