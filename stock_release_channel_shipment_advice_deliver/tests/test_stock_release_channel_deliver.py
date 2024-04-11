# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.queue_job.tests.common import trap_jobs

from .common import TestStockReleaseChannelDeliverCommon


class TestStockReleaseChannelDeliver(TestStockReleaseChannelDeliverCommon):
    def test_action_deliver_allowed(self):
        """Test action_deliver allowed."""
        self.channel.action_unlock()
        self.assertEqual(self.channel.state, "open")
        with self.assertRaises(
            UserError, msg="Action 'Deliver' is not allowed for the channel Default."
        ):
            self.channel.action_deliver()

    def test_deliver_process(self):
        """Shipment advices are created and automatically processed."""
        self._do_internal_pickings()
        with trap_jobs() as trap_rc:
            self.channel.action_deliver()
            self.assertEqual(self.channel.state, "delivering")
            trap_rc.assert_enqueued_job(self.channel._action_deliver)
            with trap_jobs() as trap_sa:
                trap_rc.perform_enqueued_jobs()
                advices = self.channel.shipment_advice_ids.filtered(
                    lambda s: s.state not in ("done", "cancel")
                )
                trap_sa.assert_enqueued_job(advices._auto_process)
                with trap_jobs() as trap_ba:
                    # this job should create a job to assign backorders to a release channel
                    trap_sa.perform_enqueued_jobs()
                    trap_ba.perform_enqueued_jobs()
                shipment_advice = advices.filtered(lambda s: s.state == "done")
        self.assertTrue(shipment_advice)
        self.assertEqual(shipment_advice.planned_pickings_count, 3)
        self.assertEqual(shipment_advice.shipment_type, "outgoing")
        self.assertEqual(shipment_advice.warehouse_id, self.wh)
        self.assertEqual(shipment_advice.state, "done")
        self.assertEqual(shipment_advice.planned_picking_ids, self.pickings)
        self.assertEqual(shipment_advice.loaded_picking_ids, self.pickings)
        self.assertTrue(shipment_advice.in_release_channel_auto_process)
        self.assertSetEqual(set(self.pickings.mapped("state")), {"done"})
        self.assertEqual(self.channel.state, "delivered")

    @mute_logger(
        "odoo.addons.stock_release_channel_shipment_advice_deliver.models.shipment_advice"
    )
    def test_deliver_error_message(self):
        """An error occurred while processing the shipment advices.

        The release channel is notified and the error is logged
        """
        self._do_internal_pickings()
        self.channel.dock_id = False
        with trap_jobs() as trap_rc:
            self.channel.action_deliver()
            self.assertEqual(self.channel.state, "delivering")
            trap_rc.assert_enqueued_job(self.channel._action_deliver)
            with trap_jobs() as trap_sa:
                trap_rc.perform_enqueued_jobs()
                shipment_advice = self.channel.shipment_advice_ids
                trap_sa.assert_enqueued_job(shipment_advice._auto_process)
                trap_sa.perform_enqueued_jobs()
        self.assertEqual(self.channel.state, "delivering_error")
        self.assertEqual(
            self.channel.delivering_error,
            f"An error occurred while processing:\n"
            f"- {shipment_advice.name}: Dock should be set on the shipment advice "
            f"{shipment_advice.name}.",
        )

    def test_deliver_retry(self):
        """Re-deliver after fail."""
        self.test_deliver_error_message()
        self.assertEqual(self.channel.state, "delivering_error")
        self.channel.dock_id = self.dock
        self.test_deliver_process()

    def test_deliver_error_empty(self):
        """No picking to deliver, an error should be raised."""
        self._do_internal_pickings()
        self.pickings.write({"release_channel_id": False})
        with self.assertRaises(
            UserError, msg="No picking to deliver for channel Default"
        ):
            self.channel.action_deliver()

    def test_deliver_backorder_not_reassigned(self):
        """
        Deliver with backorder, no other channel available:

        - the backorder should not be assigned to the channel
        - the backorder should not be assigned to the shipment advice
        """
        self._update_qty_in_location(self.output_loc, self.product2, 10)
        self.pickings.do_unreserve()
        self.pickings.action_assign()
        self.test_deliver_process()
        backorder = self.pickings.backorder_ids
        self.assertFalse(backorder.release_channel_id)
        self.assertFalse(backorder.planned_shipment_advice_id)

    def test_deliver_backorder_reassigned(self):
        """
        Deliver with backorder, another channel available:

        - the backorder should be assigned to the available channel
        - the backorder should not be assigned to the shipment advice
        """
        channel = self.channel.copy({"name": "channel 2", "state": "open"})
        self._do_internal_pickings()
        self._update_qty_in_location(self.output_loc, self.product2, 10)
        self.pickings.do_unreserve()
        self.pickings.action_assign()
        self.test_deliver_process()
        backorder = self.pickings.backorder_ids
        self.assertEqual(backorder.release_channel_id, channel)
        self.assertFalse(backorder.planned_shipment_advice_id)

    def test_deliver_fails_picking_printed(self):
        """Deliver is not allowed if one of the pickings is started."""
        self.internal_pickings[0].printed = True
        with self.assertRaises(
            UserError,
            msg="One of the pickings to deliver for channel Default is started.",
        ):
            self.channel.action_deliver()

    def test_deliver_remaining_picking_unreleased(self):
        """Deliver is allowed by a user confirmation.

        If one of the released picking is not done, the undone picking will be unreleased
        """
        self._do_picking(self.internal_pickings[0])
        self._do_picking(self.internal_pickings[1])
        not_done_picking = self.internal_pickings.filtered(
            lambda p: p.state == "assigned"
        )
        res = self.channel.action_deliver()
        self.assertIsInstance(res, dict)
        wizard = (
            self.env[res.get("res_model")].with_context(**res.get("context")).create({})
        )
        with trap_jobs() as trap_rc:
            wizard.action_deliver()
            self.assertEqual(self.channel.state, "delivering")
            trap_rc.assert_enqueued_job(self.channel._action_deliver)
            with trap_jobs() as trap_sa:
                trap_rc.perform_enqueued_jobs()
                shipment_advice = self.channel.shipment_advice_ids
                trap_sa.assert_enqueued_job(shipment_advice._auto_process)
                trap_sa.perform_enqueued_jobs()
        self.assertEqual(self.channel.state, "delivered")
        self.assertEqual(not_done_picking.state, "cancel")

    def test_deliver_fails_picking_started(self):
        """Picking started.

        Deliver is not allowed if one of the released picking is not done
        and the unrelease is not possible."""
        self._do_picking(self.internal_pickings[0])
        self._do_picking(self.internal_pickings[1])
        not_done_picking = self.internal_pickings.filtered(
            lambda p: p.state == "assigned"
        )
        not_done_picking.move_ids[0].product_uom_qty = 4
        with self.assertRaises(
            UserError,
            msg="There are some preparations that have not been completed."
            "If you choose to proceed, these preparations need to be unreleased."
            " Please handle them manually before proceeding with the delivery.",
        ):
            self.channel.action_deliver()

    def test_deliver_partial_pick_without_bo(self):
        """Partial picking without backorder creation.

        Deliver must be allowed"""
        # Process 2 out of 5
        self.internal_pickings.picking_type_id.create_backorder = "never"
        for move in self.internal_pickings[0].move_ids:
            move.quantity_done = 2
        self.internal_pickings[0].button_validate()
        res = self.channel.action_deliver()
        self.assertIsInstance(res, dict)
        wizard = (
            self.env[res.get("res_model")].with_context(**res.get("context")).create({})
        )
        wizard.with_context(test_queue_job_no_delay=True).action_deliver()
        self.assertEqual(self.channel.state, "delivered")

    def test_delivering_from_shipment_advice(self):
        self.assertEqual(self.channel.state, "locked")
        self.pickings.write({"release_channel_id": self.channel.id})
        self._do_internal_pickings()
        self.assertTrue(self.channel.is_action_deliver_allowed)
        shipment_advice = self.env["shipment.advice"].create(
            {
                "shipment_type": "outgoing",
                "release_channel_id": self.channel.id,
                "dock_id": self.channel.dock_id.id,
                "arrival_date": fields.Datetime.now(),
            }
        )
        shipment_advice.action_confirm()
        shipment_advice.action_in_progress()
        self.assertEqual(self.channel.state, "delivering")
