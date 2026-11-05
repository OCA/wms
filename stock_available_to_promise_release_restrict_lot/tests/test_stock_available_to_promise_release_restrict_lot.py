# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import TransactionCase


class TestStockAvailableToPromiseReleaseRestrictLot(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.location_wh_stock = cls.env.ref("stock.stock_location_stock")
        cls.location_customer = cls.env.ref("stock.stock_location_customers")
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "product", "tracking": "lot"}
        )
        cls.lot_1 = cls.env["stock.lot"].create(
            {"name": "Lot 1", "product_id": cls.product.id}
        )
        cls.lot_2 = cls.env["stock.lot"].create(
            {"name": "Lot 2", "product_id": cls.product.id}
        )

        # Create stock pickings and moves with different priorities
        cls.picking_1 = cls.env["stock.picking"].create(
            {
                "priority": "1",
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.location_wh_stock.id,
                "location_dest_id": cls.location_customer.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": "move 1",
                            "warehouse_id": cls.warehouse.id,
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": cls.location_wh_stock.id,
                            "location_dest_id": cls.location_customer.id,
                        }
                    )
                ],
            }
        )
        cls.move_priority_high = cls.picking_1.move_ids

        cls.picking_2 = cls.env["stock.picking"].create(
            {
                "priority": "0",
                "picking_type_id": cls.picking_type.id,
                "location_id": cls.location_wh_stock.id,
                "location_dest_id": cls.location_customer.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": "move 2",
                            "warehouse_id": cls.warehouse.id,
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": cls.location_wh_stock.id,
                            "location_dest_id": cls.location_customer.id,
                        }
                    )
                ],
            }
        )
        cls.move_priority_low = cls.picking_2.move_ids

        # Confirm and assign the pickings
        cls.picking_1.action_confirm()
        cls.picking_1.action_assign()
        cls.picking_2.action_confirm()
        cls.picking_2.action_assign()

    @classmethod
    def _update_qty_in_location(cls, location, product, quantity, lot=None):
        cls.env["stock.quant"]._update_available_quantity(
            product, location, quantity, lot_id=lot
        )
        cls.env["product.product"].invalidate_model(
            fnames=[
                "qty_available",
                "virtual_available",
                "incoming_qty",
                "outgoing_qty",
            ]
        )

    def test_0(self):
        """
        Test standard allocation behavior without lot restrictions.
        Verifies that moves with higher priority are allocated available quantities
        first.
        """
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 8, self.lot_1
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 8)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 10)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 0)

    def test_1(self):
        """
        Test a high-priority move restricted to a specific lot with no available stock
        in that lot.
        Verifies that a restricted lot move does not interfere with another move's
        allocation.
        """
        self.move_priority_high.restrict_lot_id = self.lot_2
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 8, self.lot_1
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 0)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 8)

    def test_2(self):
        """
        Test a low-priority move restricted to a specific lot without interfering with
        high-priority allocation.
        Verifies that low-priority restrictions don’t reduce available quantities
        for high-priority moves.
        """
        self.move_priority_low.restrict_lot_id = self.lot_2
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 8, self.lot_1
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 8)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 0)

    def test_3(self):
        """
        Test both moves with lot restrictions and available quantities in each lot.
        Verifies that each move is allocated quantities based on its lot restriction.
        """
        self.move_priority_high.restrict_lot_id = self.lot_1
        self.move_priority_low.restrict_lot_id = self.lot_2
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 8, self.lot_1
        )
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 5, self.lot_2
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 8)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 5)

    def test_4(self):
        """
        Test both moves with lot restrictions to the same lot.
        Verifies that each move is allocated quantities based on its lot restriction
        respecting the priority.
        """
        self.move_priority_high.restrict_lot_id = self.lot_1
        self.move_priority_low.restrict_lot_id = self.lot_1
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 15, self.lot_1
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 10)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 10)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 5)

    def test_5(self):
        """
        Test both moves with lot restrictions to the same lot with partial availability.
        Verifies that each move is allocated quantities based on its lot restriction
        respecting the priority.
        """
        self.move_priority_high.restrict_lot_id = self.lot_1
        self.move_priority_low.restrict_lot_id = self.lot_1
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 8, self.lot_1
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 8)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 10)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 0)

    def test_6(self):
        """
        Test both moves with lot restrictions to the same lot with no availability.
        Verifies that each move is allocated quantities based on its lot restriction
        respecting the priority.
        """
        self.move_priority_high.restrict_lot_id = self.lot_1
        self.move_priority_low.restrict_lot_id = self.lot_1
        self._update_qty_in_location(
            self.location_wh_stock, self.product, 8, self.lot_2
        )
        self.assertEqual(self.move_priority_high.previous_promised_qty, 0)
        self.assertEqual(self.move_priority_high.ordered_available_to_promise_qty, 0)
        self.assertEqual(self.move_priority_low.previous_promised_qty, 10)
        self.assertEqual(self.move_priority_low.ordered_available_to_promise_qty, 0)
