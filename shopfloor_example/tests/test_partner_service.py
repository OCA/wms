# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.shopfloor_base.tests.common import CommonCase


class TestCustomServiceCase(CommonCase):
    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        cls.shopfloor_user.groups_id += cls.env.ref("base.group_partner_manager")

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.record = cls.env.ref("base.res_partner_4")
        cls.record.ref = "1234"

    def _get_service(self):
        with self.work_on_services() as work:
            return work.component(usage="partner_example")

    def test_partner_data(self):
        self.assertEqual(
            self.data_detail.partner(self.record),
            {"id": self.record.id, "name": self.record.name},
        )

    def test_partner_data_detail(self):
        self.assertEqual(
            self.data_detail.partner_detail(self.record),
            {
                "id": self.record.id,
                "name": self.record.name,
                "ref": self.record.ref,
                "email": self.record.email,
            },
        )

    def test_scan(self):
        service = self._get_service()
        identifier = self.record.ref
        res = service.dispatch("scan", identifier)
        self.assertEqual(
            res,
            {
                "data": {
                    "detail": {"record": self.data_detail.partner_detail(self.record)}
                },
                "next_state": "detail",
            },
        )

    def test_listing(self):
        service = self._get_service()
        all_records = self.env["res.partner"].search([])
        res = service.dispatch("partner_list")
        self.assertEqual(
            res,
            {
                "data": {"listing": {"records": self.data.partners(all_records)}},
                "next_state": "listing",
            },
        )
