# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class ReleaseChannelPlanCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plan1 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_preparation_plan_demo_mon"
        )
        cls.plan1_channel1 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_mon_thu1"
        )
        cls.plan1_channel2 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_mon_thu2"
        )
        cls.plan2_channel1 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_tue_fri1"
        )
        cls.plan2_channel2 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_tue_fri2"
        )
        cls.plan3_channel1 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_wed1"
        )
        cls.plan3_channel2 = cls.env.ref(
            "stock_release_channel_plan.stock_release_channel_wed2"
        )

    def _launch_channel(self, preparation_plan):
        self.env["stock.release.channel.plan.wizard.launch"].create(
            {
                "preparation_plan_id": preparation_plan.id,
            }
        ).action_launch()
