# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestDataForPicking(CommonCase):
    def test_data_for_picking(self):
        picking = self._create_picking()
        data = self.service._data_for_stock_picking(picking)
        expected = self.data.picking(
            picking, **{"with_progress": True, "with_purchase_order": True}
        )
        self.assertDictEqual(expected, data)
