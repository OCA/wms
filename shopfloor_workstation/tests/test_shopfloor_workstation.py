# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.shopfloor.tests.common import CommonCase


class ShopfloorWorkstationCase(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pserver = cls.env["printing.server"].sudo().create({})
        printer_vals = {
            "name": "P-One",
            "server_id": cls.pserver.id,
            "system_name": "Sys Name",
            "default": True,
            "status": "unknown",
            "status_message": "Msg",
            "model": "res.users",
            "location": "Location",
            "uri": "URI",
        }
        cls.printer1 = cls.env["printing.printer"].sudo().create(printer_vals)
        printer_vals["name"] = "P-Two"
        cls.printer2 = cls.env["printing.printer"].sudo().create(printer_vals)
        cls.ws1 = cls.env.ref("shopfloor_workstation.ws_pollux")
        cls.ws1.sudo().printing_printer_id = cls.printer1
        cls.profile1 = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.ws1.sudo().shopfloor_profile_id = cls.profile1

    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
            self.service = work.component(usage="workstation")

    def test_workstation_set_default_not_found(self):
        res = self.service.dispatch("setdefault", params={"barcode": "bc-???"})
        self.assert_response(
            res,
            message={"body": "Workstation not found", "message_type": "error"},
            data={},
        )

    def test_workstation_set_default_found(self):
        self.assertFalse(self.env.user.printing_printer_id)
        res = self.service.dispatch("setdefault", params={"barcode": "ws-1"})
        self.assert_response(
            res,
            message={
                "body": "Default workstation set to Pollux",
                "message_type": "info",
            },
            data={
                "id": self.ws1.id,
                "name": "Pollux",
                "barcode": "ws-1",
                "profile": {
                    "id": self.ws1.shopfloor_profile_id.id,
                    "name": self.ws1.shopfloor_profile_id.name,
                },
            },
        )
        self.assertEqual(self.env.user.printing_printer_id, self.printer1)
