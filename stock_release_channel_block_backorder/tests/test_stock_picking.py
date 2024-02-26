# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import CommonReleaseChannelBlock


class TestStockPicking(CommonReleaseChannelBlock):
    def test_00(self):
        """Create backorder and check that it's flagged as full backorder."""
        picking = self._create_picking_out(product_qty=120)
        self._do_picking(picking, 100)
        self.assertEqual(picking.state, "done")
        backorder = picking.backorder_ids
        self.assertTrue(backorder.move_ids.delivery_requires_other_lines)
        product_qty_unavailable = (
            backorder.move_ids.product_qty
            - backorder.move_ids.ordered_available_to_promise_qty
        )
        self.assertEqual(product_qty_unavailable, 20)
        self.assertTrue(backorder.delivery_requires_other_lines)
        self.assertTrue(backorder.blocked_for_channel_assignation)

    def test_01(self):
        """Check that a full backorder became a regular picking if new move is added."""
        picking = self._create_picking_out(product_qty=120)
        self._do_picking(picking, 100)
        backorder = picking.backorder_ids
        self.env["stock.move"].create(
            {
                "picking_id": backorder.id,
                "name": "Delivery move",
                "product_id": self.product.id,
                "product_uom_qty": 120,
                "product_uom": self.product.uom_id.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customer.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )
        self.assertFalse(backorder.delivery_requires_other_lines)
        self.assertFalse(backorder.blocked_for_channel_assignation)

    def test_02(self):
        """Check that a full back order can't be assigned to a release channel."""
        picking = self._create_picking_out(product_qty=120)
        self._do_picking(picking, 100)
        backorder = picking.backorder_ids
        backorder.assign_release_channel()
        self.assertFalse(backorder.release_channel_id)

    def test_03(self):
        """Check that a mixed back order can be assigned to a release channel."""
        picking = self._create_picking_out(product_qty=120)
        self._do_picking(picking, 100)
        backorder = picking.backorder_ids
        self.env["stock.move"].create(
            {
                "picking_id": backorder.id,
                "name": "Delivery move",
                "product_id": self.product.id,
                "product_uom_qty": 120,
                "product_uom": self.product.uom_id.id,
                "location_id": self.loc_stock.id,
                "location_dest_id": self.loc_customer.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )
        backorder.assign_release_channel()
        self.assertTrue(backorder.release_channel_id)

    def test_04(self):
        """Check that a full back order can be assigned to a release channel if user.

        force it
        """
        picking = self._create_picking_out(product_qty=120)
        self._do_picking(picking, 100)
        backorder = picking.backorder_ids
        backorder.button_ignore_release_channel_block()
        self.assertTrue(backorder.release_channel_id)
        self.assertFalse(backorder.blocked_for_channel_assignation)

    def test_05(self):
        """Create backorder even if the product is available.

        The backorder should be assigned and not flagged as full back order.
        """
        picking = self._create_picking_out(product_qty=100)
        self._do_picking(picking, 80)
        self.assertEqual(picking.state, "done")
        backorder = picking.backorder_ids
        self.assertFalse(backorder.move_ids.delivery_requires_other_lines)
        product_qty_unavailable = (
            backorder.move_ids.product_qty
            - backorder.move_ids.ordered_available_to_promise_qty
        )
        self.assertEqual(product_qty_unavailable, 0)
        self.assertFalse(backorder.delivery_requires_other_lines)
        backorder.assign_release_channel()
        self.assertTrue(backorder.release_channel_id)
