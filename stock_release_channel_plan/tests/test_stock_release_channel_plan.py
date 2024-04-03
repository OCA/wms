# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import ReleaseChannelPlanCase


class TestStockReleaseChannelPlan(ReleaseChannelPlanCase):
    def test_launch_plan(self):
        """Test launching plan1"""
        self.plan1_channel1.write({"state": "locked"})
        self.plan1_channel2.write({"state": "asleep"})
        self.plan2_channel1.write({"state": "locked"})
        self.plan2_channel2.write({"state": "asleep"})
        self.plan3_channel1.write({"state": "open"})
        self.plan3_channel2.write({"state": "open"})

        self._launch_channel(self.plan1)

        self.assertEqual(self.plan1_channel1.state, "open")
        self.assertEqual(self.plan1_channel2.state, "open")
        self.assertEqual(self.plan2_channel1.state, "locked")
        self.assertEqual(self.plan2_channel2.state, "asleep")
        self.assertEqual(self.plan3_channel1.state, "open")
        self.assertEqual(self.plan3_channel2.state, "open")
