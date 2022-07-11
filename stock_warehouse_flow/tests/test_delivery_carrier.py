# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from . import common


class TestDeliveryCarrier(common.CommonFlow):
    def test_action_view_flows(self):
        flow = self._get_flow("pick_ship")
        action = flow.carrier_ids.action_view_flows()
        self.assertEqual(action["domain"][0][2], flow.ids)
