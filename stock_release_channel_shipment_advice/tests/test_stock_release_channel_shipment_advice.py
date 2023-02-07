# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.exceptions import UserError

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
