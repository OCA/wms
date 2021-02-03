# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.tests.common import SavepointCase


class TestShopfloorPackingInfo(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.packing_info = cls.env["shopfloor.packing.info"].create(
            {"name": "Test Name", "text": "Test Text"}
        )

    def test_unlink(self):
        partner = self.env["res.partner"].create(
            {"name": "Partner", "shopfloor_packing_info_id": self.packing_info.id}
        )
        self.assertTrue(self.packing_info.active)
        self.assertEqual(partner.shopfloor_packing_info_id, self.packing_info)
        self.packing_info.unlink()
        self.assertFalse(self.packing_info.active)
        self.assertEqual(partner.shopfloor_packing_info_id, self.packing_info)

    def test_toggle_active(self):
        self.assertTrue(self.packing_info.active)
        self.packing_info.toggle_active()
        self.assertFalse(self.packing_info.active)
        self.packing_info.toggle_active()
        self.assertTrue(self.packing_info.active)
