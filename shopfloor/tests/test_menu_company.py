# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from unittest import mock

from odoo.tests.common import TransactionCase

from odoo.addons.shopfloor_base.controllers.main import ShopfloorController


class TestMenuCompany(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company2 = cls.env["res.company"].create({"name": "Shopfloor Company 2"})
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_delivery")
        warehouse2 = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company2.id)], limit=1
        )
        cls.picking_type2 = cls.menu.picking_type_ids[0].copy(
            {
                "company_id": cls.company2.id,
                "warehouse_id": warehouse2.id,
                "default_location_src_id": warehouse2.lot_stock_id.id,
                "default_location_dest_id": warehouse2.lot_stock_id.id,
                "return_picking_type_id": False,
            }
        )
        cls.menu.picking_type_ids = cls.picking_type2
        cls.env.user.company_ids |= cls.company2
        cls.app = cls.env.ref("shopfloor.app_demo")

    def _get_collection_env_context(self, headers):
        request = mock.MagicMock()
        request.httprequest.environ = headers
        with mock.patch("odoo.addons.shopfloor_base.controllers.main.request", request):
            return ShopfloorController()._get_collection_env_context(self.app, {})

    def test_get_allowed_companies(self):
        self.assertEqual(self.menu._get_allowed_companies(), self.company2)

    def test_env_context_menu(self):
        ctx = self._get_collection_env_context(
            {"HTTP_SERVICE_CTX_MENU_ID": str(self.menu.id)}
        )
        self.assertEqual(ctx["allowed_company_ids"], self.company2.ids)

    def test_env_context_menu_company_not_allowed(self):
        self.env.user.company_ids -= self.company2
        ctx = self._get_collection_env_context(
            {"HTTP_SERVICE_CTX_MENU_ID": str(self.menu.id)}
        )
        self.assertNotIn("allowed_company_ids", ctx)

    def test_env_context_no_menu(self):
        ctx = self._get_collection_env_context({})
        self.assertNotIn("allowed_company_ids", ctx)
        ctx = self._get_collection_env_context({"HTTP_SERVICE_CTX_MENU_ID": "abc"})
        self.assertNotIn("allowed_company_ids", ctx)
