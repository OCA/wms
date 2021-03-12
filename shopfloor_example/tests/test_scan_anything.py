# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.shopfloor_base.tests.common import CommonCase
from odoo.addons.shopfloor_base.tests.common_misc import ScanAnythingTestMixin


class ScanAnythingCase(CommonCase, ScanAnythingTestMixin):
    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        cls.shopfloor_user.groups_id += cls.env.ref("base.group_partner_manager")

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.record = cls.env.ref("base.res_partner_4")
        cls.record.ref = "1234"

    def test_scan(self):
        record = self.record
        record.ref = "1234"
        rec_type = "partner_example"
        identifier = record.ref
        data = self.data_detail.partner_detail(record)
        self._test_response_ok(rec_type, data, identifier, record_types=(rec_type,))

    def test_scan_error(self):
        self._test_response_ko("WRONG-REF", record_types=("partner_example",))
