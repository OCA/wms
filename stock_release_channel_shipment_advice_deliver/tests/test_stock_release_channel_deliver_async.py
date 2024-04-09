# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.tools import mute_logger

from odoo.addons.queue_job.tests.common import trap_jobs

from .common import TestStockReleaseChannelDeliverCommon


class TestStockReleaseChannelDeliverAsync(TestStockReleaseChannelDeliverCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.company_id.shipment_advice_run_in_queue_job = True

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
                with trap_jobs() as trap_sap:
                    # picking jobs
                    trap_sa.perform_enqueued_jobs()
                    trap_sap.assert_jobs_count(5)
                    # 3 picking + 1 for unplan + 1 for postprocess
                    with trap_jobs() as trap_ba:
                        # this job should create a job to assign backorders to a release channel
                        trap_sap.perform_enqueued_jobs()
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
                advices = self.channel.shipment_advice_ids.filtered(
                    lambda s: s.state not in ("done", "cancel")
                )
                trap_sa.assert_enqueued_job(advices._auto_process)
                with trap_jobs() as trap_sap:
                    # picking jobs
                    trap_sa.perform_enqueued_jobs()
                    trap_sap.assert_jobs_count(4)
                    # 2 picking + 1 for unplan + 1 for postprocess
                    with trap_jobs() as trap_ba:
                        # this job should create a job to assign backorders to a release channel
                        trap_sap.perform_enqueued_jobs()
                        trap_ba.perform_enqueued_jobs()
                advices.filtered(lambda s: s.state == "done")
        self.assertEqual(self.channel.state, "delivered")
        self.assertEqual(not_done_picking.state, "cancel")

    def _process_deliver_jobs(self, expected_jobs_count):
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
                with trap_jobs() as trap_sap:
                    # picking jobs
                    trap_sa.perform_enqueued_jobs()
                    # number pickings + 1 for unplan + 1 for postprocess
                    trap_sap.assert_jobs_count(expected_jobs_count)

                    with trap_jobs() as trap_ba:
                        # this job should create a job to assign backorders to a release channel
                        trap_sap.perform_enqueued_jobs()
                        trap_ba.perform_enqueued_jobs()
        return advices

    def test_deliver_retry_after_partial_fail(self):
        """Retry deliver from release channel after partial fail."""
        self._do_internal_pickings()
        picking = self.channel.picking_to_plan_ids[0]
        package = self.env["stock.quant.package"].create({})
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 2, package_id=package
        )
        picking.move_line_ids.result_package_id = package
        shipment_advice = self._process_deliver_jobs(
            expected_jobs_count=5
        )  # 3 pickings to do
        self.assertEqual(shipment_advice.state, "error")
        self.assertEqual(self.channel.state, "delivering_error")
        self.assertEqual(picking.state, "assigned")
        picking.move_line_ids.result_package_id = False
        self._process_deliver_jobs(expected_jobs_count=3)  # 1 picking remaining
        self.assertEqual(self.channel.state, "delivered")
        self.assertEqual(picking.state, "done")
        self.assertEqual(shipment_advice.state, "done")

    def test_deliver_retry_from_shipment_advice(self):
        """Retry deliver from shipment advice after partial fail."""
        self._do_internal_pickings()
        picking = self.channel.picking_to_plan_ids[0]
        package = self.env["stock.quant.package"].create({})
        self.env["stock.quant"]._update_available_quantity(
            self.product1, self.loc_stock, 2, package_id=package
        )
        picking.move_line_ids.result_package_id = package
        shipment_advice = self._process_deliver_jobs(
            expected_jobs_count=5
        )  # 3 pickings to do
        self.assertEqual(shipment_advice.state, "error")
        self.assertEqual(self.channel.state, "delivering_error")
        self.assertEqual(picking.state, "assigned")
        picking.move_line_ids.result_package_id = False
        with trap_jobs() as trap_sap:
            shipment_advice.action_done()
            self.assertEqual(self.channel.state, "delivering")
            self.assertEqual(shipment_advice.state, "in_process")
            # picking jobs
            # number pickings + 1 for unplan + 1 for postprocess
            trap_sap.assert_jobs_count(3)
            trap_sap.perform_enqueued_jobs()
        self.assertEqual(self.channel.state, "delivered")
        self.assertEqual(picking.state, "done")
        self.assertEqual(shipment_advice.state, "done")
