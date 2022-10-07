# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from . import common


class TestWarehouse(common.CommonFlow):
    def test_action_view_all_flows(self):
        action = self.wh.action_view_all_flows()
        self.assertTrue(self.wh.flow_ids)
        self.assertEqual(action["domain"][0][2], self.wh.flow_ids.ids)
