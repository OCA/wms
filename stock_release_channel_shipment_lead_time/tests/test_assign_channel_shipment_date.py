# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo import fields
from odoo.tests.common import Form

from odoo.addons.queue_job.tests.common import trap_jobs
from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase


class TestReleaseChannel(ReleaseChannelCase):
    def test_shipment_advice_planner(self):
        # deactive all existing channels before testing
        all_default_channel = self.env["stock.release.channel"].search(
            [("state", "!=", "asleep")]
        )
        all_default_channel.action_sleep()

        # create a testing lead time without calendar
        #  => shipment_date = 2023-07-06
        self._create_channel(
            name="Test Shipment Lead Time",
            sequence=1,
            process_end_date="2023-06-30",
            shipment_lead_time=6,
        )

        # create a picking with deadline <= channel shipment date = 2023-07-06
        self._update_qty_in_location(
            self.wh.out_type_id.default_location_src_id,
            self.product1,
            20,
        )
        move = self._create_single_move(self.product1, 10)
        move.date_deadline = "2023-07-03 00:00:00"
        move.picking_id.action_assign()
        with trap_jobs() as trap:
            picking = move.picking_id
            picking._delay_assign_release_channel()
            trap.assert_jobs_count(1, only=picking.assign_release_channel)
            trap.perform_enqueued_jobs()

        self.context = {
            "active_ids": [picking.id],
            "active_model": "stock.picking",
        }
        self.wizard_form = Form(
            self.env["shipment.advice.planner"].with_context(**self.context)
        )
        self.wizard_form.warehouse_id = self.wh
        self.wizard_form.picking_to_plan_ids.add(picking)
        wizard = self.wizard_form.save()
        action = wizard.button_plan_shipments()
        shipment = self.env[action.get("res_model")].search(action.get("domain"))
        self.assertEqual(len(shipment), 1)
        self.assertEqual(
            "2023-07-06",
            fields.Date.to_string(shipment.delivery_date),
        )

    def test_assign_channel_with_shipment_date(self):
        # deactive all existing channels before testing
        all_default_channel = self.env["stock.release.channel"].search(
            [("state", "!=", "asleep")]
        )
        all_default_channel.action_sleep()

        # create a testing lead time without calendar
        #  => shipment_date = 2023-07-06
        self._create_channel(
            name="Test Shipment Lead Time",
            sequence=1,
            process_end_date="2023-06-30",
            shipment_lead_time=6,
        )

        # create a picking with deadline <= channel shipment date = 2023-07-06
        move = self._create_single_move(self.product1, 10)
        move.date_deadline = "2023-07-06 00:00:00"
        with trap_jobs() as trap:
            picking = move.picking_id
            picking._delay_assign_release_channel()
            trap.assert_jobs_count(1, only=picking.assign_release_channel)
            trap.perform_enqueued_jobs()

        self.assertTrue(picking.release_channel_id)

        # create a picking with deadline > channel shipment date = 2023-07-06
        move = self._create_single_move(self.product1, 10)
        move.date_deadline = "2023-07-07 00:00:00"
        with trap_jobs() as trap:
            picking = move.picking_id
            picking._delay_assign_release_channel()
            trap.assert_jobs_count(1, only=picking.assign_release_channel)
            trap.perform_enqueued_jobs()

        self.assertFalse(picking.release_channel_id)
