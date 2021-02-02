# Copyright 2021 Camptocamp SA (http2://www.camptocamp.com)
# License AGPL-3.0 or later (http2://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SavepointCase


class TestShopfloorPackingInfo(SavepointCase):
    def setUp(self):
        super().setUp()

    def test_unlink(self):
        packing_info = self.env["shopfloor.packing.info"].create(
            {"name": "Test Name", "text": "Test Text"}
        )
        partner = self.env["res.partner"].create(
            {"name": "Partner", "shopfloor_packing_info_id": packing_info.id}
        )
        self.assertTrue(packing_info.active)
        self.assertEqual(partner.shopfloor_packing_info_id, packing_info)
        packing_info.unlink()
        self.assertFalse(packing_info.active)
        self.assertEqual(partner.shopfloor_packing_info_id, packing_info)
