# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from vcr_unittest import VCRTestCase

from odoo.addons.stock_release_channel.tests.common import ChannelReleaseCase


class TestShipmentAdvicePlannerToursolver(VCRTestCase, ChannelReleaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.resource_1 = cls.env.ref(
            "shipment_advice_planner_toursolver.toursolver_resource_r1_demo"
        )
        cls.resource_2 = cls.env.ref(
            "shipment_advice_planner_toursolver.toursolver_resource_r2_demo"
        )

        (cls.picking + cls.picking2 + cls.picking3).unlink()
        cls.pickings = cls.env["stock.picking"].search(
            [("picking_type_code", "=", "outgoing"), ("partner_id", "!=", False)]
        )
        cls.channel.picking_ids = cls.pickings
        cls.pickings.move_ids.write({"procure_method": "make_to_stock"})
        cls.pickings.action_assign()
        cls.channel.shipment_planning_method = "toursolver"
        cls.channel.delivery_resource_ids = cls.resource_1 | cls.resource_2

    def test_plan_shipment_toursolver(self):
        pickings = self.channel.picking_to_plan_ids
        self.channel.button_plan_shipments()
        self.assertFalse(self.channel.shipment_advice_ids)
        self.assertEqual(len(pickings.toursolver_task_id), 1)
        task = pickings.toursolver_task_id
        task.button_send_request()
        self.assertEqual(task.state, "in_progress")
        self.assertFalse(task.toursolver_error_message)
        task.button_check_status()
        self.assertEqual(task.state, "success")
        task.button_get_result()
        self.assertEqual(task.state, "done")
        self.assertEqual(
            task.shipment_advice_ids.toursolver_resource_id, self.resource_2
        )
        self.assertTrue(self.channel.shipment_advice_ids)
        self.assertEqual(self.channel.shipment_advice_ids, task.shipment_advice_ids)
        self.assertEqual(task.release_channel_id, self.channel)
