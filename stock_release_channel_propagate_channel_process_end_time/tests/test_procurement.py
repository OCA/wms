# Copyright 2022 ACSONE SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.stock_release_channel_propagate_channel_picking.tests.test_procurement import (
    TestReleaseChannelProcurement,
)


class TestReleaseChannelPropagation(TestReleaseChannelProcurement):
    def test_channel_internal_propagation(self):
        pickings_internal = super().test_channel_internal_propagation()
        self.assertEqual(
            pickings_internal.scheduled_date,
            pickings_internal.release_channel_id.process_end_date,
        )
        return pickings_internal
