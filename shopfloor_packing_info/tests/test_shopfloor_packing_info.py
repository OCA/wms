# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from psycopg2 import IntegrityError

from odoo.tests.common import SavepointCase
from odoo.tools import mute_logger


class TestShopfloorPackingInfo(SavepointCase):
    def test_unlink(self):
        packing_info = self.env["shopfloor.packing.info"].create(
            {"name": "Test Name", "text": "Test Text"}
        )
        partner = self.env.ref("base.res_partner_3")
        partner.shopfloor_packing_info_id = packing_info
        self.assertTrue(packing_info.active)
        self.assertEqual(partner.shopfloor_packing_info_id, packing_info)
        with mute_logger("odoo.sql_db"):
            with self.assertRaises(IntegrityError):
                packing_info.unlink()
