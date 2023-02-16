# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestStockReleaseChannelShipmentAdvice(ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        output_loc = cls.channel.picking_ids.move_ids.location_id
        cls._update_qty_in_location(output_loc, cls.product1, 100)
        cls._update_qty_in_location(output_loc, cls.product2, 100)
        cls.channel.picking_ids.move_ids.write({"procure_method": "make_to_stock"})
        cls.channel.picking_ids.action_assign()
        cls.dock = cls.env.ref("shipment_advice.stock_dock_demo")
        cls.dock.warehouse_id = cls.wh
        cls.warehouse2 = cls.env.ref("stock.stock_warehouse_shop0")

    def test_can_plan_shipment(self):
        """plan shipment isn't allowed when the planning method is none or when no
        picking to plan"""
        self.channel.shipment_planning_method = "none"
        self.assertFalse(self.channel.can_plan_shipment)
        with self.assertRaises(UserError):
            self.channel.button_plan_shipments()
        self.channel.shipment_planning_method = "simple"
        self.assertTrue(self.channel.picking_to_plan_ids)
        self.assertTrue(self.channel.can_plan_shipment)
        self.assertFalse(self.channel.shipment_advice_ids)
        self.channel.button_plan_shipments()
        self.assertTrue(self.channel.shipment_advice_ids)
        self.assertFalse(self.channel.picking_to_plan_ids)
        self.assertFalse(self.channel.can_plan_shipment)

    def test_plan_shipment_simple(self):
        self.channel.shipment_planning_method = "simple"
        pickings = self.channel.picking_to_plan_ids
        self.channel.button_plan_shipments()
        shipment_advice = self.channel.shipment_advice_ids
        self.assertTrue(shipment_advice)
        self.assertEqual(shipment_advice.planned_picking_ids, pickings)
        self.assertEqual(shipment_advice.planned_pickings_count, 3)
        self.assertEqual(shipment_advice.shipment_type, "outgoing")
        self.assertEqual(shipment_advice.warehouse_id, self.wh)

    def test_plan_shipment_simple_with_dock(self):
        self.channel.shipment_planning_method = "simple"
        self.channel.dock_id = self.dock
        pickings = self.channel.picking_to_plan_ids
        self.channel.button_plan_shipments()
        shipment_advice = self.channel.shipment_advice_ids
        self.assertTrue(shipment_advice)
        self.assertEqual(shipment_advice.planned_picking_ids, pickings)
        self.assertEqual(shipment_advice.planned_pickings_count, 3)
        self.assertEqual(shipment_advice.shipment_type, "outgoing")
        self.assertEqual(shipment_advice.warehouse_id, self.wh)
        self.assertEqual(shipment_advice.dock_id, self.dock)

    def test_release_channel_unset_dock_1(self):
        channel_form = Form(self.channel)
        with self.assertRaises(
            AssertionError, msg="can't write on invisible field dock_id"
        ):
            channel_form.dock_id = self.dock
        channel_form.warehouse_id = self.wh
        channel_form.dock_id = self.dock
        channel_form.warehouse_id = self.env["stock.warehouse"]
        channel_form.warehouse_id = self.wh
        self.assertFalse(channel_form.dock_id)

    def test_release_channel_unset_dock_2(self):
        self.channel.write({"warehouse_id": self.wh.id, "dock_id": self.dock.id})
        self.assertEqual(self.channel.dock_id, self.dock)
        self.channel.warehouse_id = False
        self.assertFalse(self.channel.dock_id)

    def test_check_warehouse(self):
        channel_form = Form(self.channel)
        channel_form.warehouse_id = self.warehouse2
        with self.assertRaises(
            ValidationError, msg="The dock doesn't belong to the selected warehouse"
        ):
            channel_form.dock_id = self.dock
        with self.assertRaises(
            ValidationError, msg="The dock doesn't belong to the selected warehouse"
        ):
            channel_form.save()
